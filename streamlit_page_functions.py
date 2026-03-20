import streamlit as st
from db_functions import connect_mongodb, mongodb_filter_by_user_and_category, mongodb_save_image_and_metadata 
from db_functions import connect_supabase, supabase_add_new_user, supabase_authenticate
from db_functions import connect_s3, s3_upload_image_and_notify
from datetime import datetime
from PIL import Image
import io
import time
import math
import ast
import os

max_retries = 5

def register_page():
    st.title('Registration Page')
    username = st.text_input('Username')
    mobile_number = st.text_input('Mobile Number')
    password = st.text_input('Password', type='password')
    confirm_password = st.text_input('Confirm Password', type='password')

    if st.button('Register'):
        if username and mobile_number and password and password == confirm_password:
            supabase_client = connect_supabase()
            successful_user_add = supabase_add_new_user(supabase_client, username, password, mobile_number)
            
            if successful_user_add:
                st.success('Registration successful! Please login...')
                st.session_state.page = 'login'
            else:
                st.error('The username you entered is already taken. Please try another username.')
        
        elif password != confirm_password:
            st.error('Passwords do not match. Please re-enter...')
        else:
            st.error('Please enter both username and password.')


def login_page():
    st.title('Login Page')
    username = st.text_input('Username')
    password = st.text_input('Password', type='password')

    if st.button('Login'):
        if supabase_authenticate(username, password):
            st.session_state.authenticated = True
            st.success('Login successful!')
            st.session_state.page = 'image_uploader'
            st.session_state.USERNAME = username

        else:
            st.error('Invalid username or password')


def image_page():
    if 'authenticated' in st.session_state and st.session_state.authenticated:
        _, clothes_db = connect_mongodb()
        collection = clothes_db['items']
        st.title("📷 Mobile Image Uploader")

        # 1) Take a photo
        shot = st.camera_input("Take a photo")

        # 2) Or pick from gallery/files
        uploads = st.file_uploader(
            "Or choose from gallery",
            type=["png","jpg","jpeg","webp","gif"],
            accept_multiple_files=True
        )

        # Handle camera capture
        if shot:
            item_id, item_path = mongodb_save_image_and_metadata(collection, st.session_state.USERNAME, shot.getvalue())
            if item_id:
                successful_img_upload = s3_upload_image_and_notify(item_path, st.session_state.USERNAME)
                if successful_img_upload:
                    os.remove(os.path.join('tempImages', item_path))
                    st.success('Successfully added image to the database! :)')
            else:
                st.warning('Failed to save camera image to database.')

        # Handle file uploads
        if uploads:
            for upload in uploads:
                raw_data = upload.getvalue()
                item_id, item_path = mongodb_save_image_and_metadata(collection, st.session_state.USERNAME, raw_data)
                if item_id:
                    successful_img_upload = s3_upload_image_and_notify(item_path, st.session_state.USERNAME)
                    if successful_img_upload:
                        os.remove(os.path.join('tempImages', item_path))
                        st.success('Successfully added image to the database! :)')
                else:
                    st.warning(f'Failed to save uploaded file "{upload.name}" to database.')

    if st.button('Logout'):
        st.session_state.authenticated = False
        st.session_state.page = 'login'
        st.success('Successfully logged out.')


def selector_page():
    if 'authenticated' in st.session_state and st.session_state.authenticated:
        st.title("💃 Outfit Selector")

        # Initialize dictionary to store all items loaded into page
        ALL_ITEMS = {}

        # Get image IDs from MongoDB based on clothing category and user
        top_img_ids = mongodb_filter_by_user_and_category(st.session_state.USERNAME, 'top')
        bottom_img_ids = mongodb_filter_by_user_and_category(st.session_state.USERNAME, 'bottom')

        # Connect to S3 bucket
        bucketname = os.environ['S3_BUCKET_NAME']
        s3_resource = connect_s3('resource')
        s3_client = connect_s3('client')
        bucket = s3_resource.Bucket(bucketname)
        
        # Filter out all keys from bucket under corresponding username
        user_image_keys = [obj.key for obj in bucket.objects.filter(Prefix=st.session_state.USERNAME)]

        def find_s3_key(img_id, keys):
            for k in keys:
                if img_id in k:
                    return k
            return None
        
        def create_s3_presigned_img_urls_list(keys_list, id_list, client, bucket_name, main_category):    
            if not main_category in ALL_ITEMS:
                ALL_ITEMS[main_category] = []
            
            # Map IDs to S3 keys to filter according to main clothing category and remove None values
            corresponding_keys = [find_s3_key(id_, keys_list) for id_ in id_list]
            corresponding_keys = [k for k in corresponding_keys if k]

            # Process pre-signed URL from provided keys
            for key in corresponding_keys:
                url = client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket_name, 'Key': key},
                    ExpiresIn=3600
                )
                temp_item = {'id': key.split('_')[0], 'url': url}
                ALL_ITEMS[main_category].append(temp_item)

        create_s3_presigned_img_urls_list(user_image_keys, top_img_ids, s3_client, os.environ['S3_BUCKET_NAME'], 'top')
        create_s3_presigned_img_urls_list(user_image_keys, bottom_img_ids, s3_client, os.environ['S3_BUCKET_NAME'], 'bottom')

        # # Map IDs to S3 keys to filter according to main clothing category
        # top_keys = [find_s3_key(id_, user_image_keys) for id_ in top_img_ids]
        # bottom_keys = [find_s3_key(id_, user_image_keys) for id_ in bottom_img_ids]

        # # Remove None values
        # top_keys = [k for k in top_keys if k]
        # bottom_keys = [k for k in bottom_keys if k]

        # # Process tops
        # for key in top_keys:
        #     url = s3_client.generate_presigned_url(
        #         'get_object',
        #         Params={'Bucket': bucketname, 'Key': key},
        #         ExpiresIn=3600
        #     )
        #     temp_item = {'id': key.split('_')[0], 'url': url}
        #     all_items['top'].append(temp_item)

        # # Process bottoms
        # for key in bottom_keys:
        #     url = s3_client.generate_presigned_url(
        #         'get_object',
        #         Params={'Bucket': bucketname, 'Key': key},
        #         ExpiresIn=3600
        #     )
        #     temp_item = {'id': key.split('_')[0], 'url': url}
        #     all_items['bottom'].append(temp_item)

        # Page configuration
        st.set_page_config(page_title="Outfit Selector", layout="wide", initial_sidebar_state="collapsed")

        # Custom CSS
        with open('selection.css', 'r') as f:
            css_style = f.read()
        st.markdown(f"""
            <style>
            {css_style}
            </style>
        """, unsafe_allow_html=True)

        # Initialize session state
        if 'current_category' not in st.session_state:
            st.session_state.current_category = 'top'
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 1
        if 'selected_item' not in st.session_state:
            st.session_state.selected_item = None

        # # Sample data - replace with your actual S3 URLs
        # # Format: {'id': 'unique_id', 'url': 'presigned_url', 'category': 'top'/'bottom'}
        # def get_clothing_items(category):
        #     """Replace this with your actual S3 data fetching logic"""
        #     # Example data structure
        #     sample_data = {
        #         'top': [
        #             {'id': f'top_{i}', 'url': f'https://via.placeholder.com/300x400/FFB6C1/000000?text=Top+{i}', 'category': 'top'}
        #             for i in range(1, 25)  # 24 sample tops
        #         ],
        #         'bottom': [
        #             {'id': f'bottom_{i}', 'url': f'https://via.placeholder.com/300x400/87CEEB/000000?text=Bottom+{i}', 'category': 'bottom'}
        #             for i in range(1, 15)  # 14 sample bottoms
        #         ]
        #     }
        #     return sample_data.get(category, [])

        # Get items for current category
        # all_items = get_clothing_items(st.session_state.current_category)

        # Get items for CURRENT CATEGORY (not all items)
        category_items = ALL_ITEMS[st.session_state.current_category]

        # Calculate pagination based on current category
        items_per_page = 20
        total_pages = math.ceil(len(category_items) / items_per_page) if category_items else 1

        # Ensure current page is valid
        if st.session_state.current_page > total_pages:
            st.session_state.current_page = total_pages

        # Get items for current page from current category
        start_idx = (st.session_state.current_page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        current_items = category_items[start_idx:end_idx] 

        # Main layout
        col1, col2 = st.columns([3, 1])

        with col1:
            # Category filter
            st.markdown('<div class="category-filter">', unsafe_allow_html=True)
            filter_col1, filter_col2 = st.columns(2)
            
            with filter_col1:
                if st.button('👕 Tops', key='tops_btn', use_container_width=True):
                    st.session_state.current_category = 'top'
                    st.session_state.current_page = 1
                    st.rerun()
            
            with filter_col2:
                if st.button('👖 Bottoms', key='bottoms_btn', use_container_width=True):
                    st.session_state.current_category = 'bottom'
                    st.session_state.current_page = 1
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Display current category
            category_emoji = '👕' if st.session_state.current_category == 'top' else '👖'
            category_name = 'Tops' if st.session_state.current_category == 'top' else 'Bottoms'
            st.markdown(f"### {category_emoji} {category_name}")
            
            # Clothing grid
            if current_items:
                # Create 5 rows of 4 columns
                for row in range(5):
                    cols = st.columns(4)
                    for col_idx, col in enumerate(cols):
                        item_idx = row * 4 + col_idx
                        if item_idx < len(current_items):
                            item = current_items[item_idx]
                            with col:
                                if st.button('', key=f"item_{item['id']}", use_container_width=True):
                                    st.session_state.selected_item = item
                                st.image(item['url'], use_container_width=True)
            else:
                st.info(f"No {category_name.lower()} found.")
            
            # Pagination
            st.markdown('<div class="pagination">', unsafe_allow_html=True)
            pagination_cols = st.columns([1, 2, 1])
            
            with pagination_cols[0]:
                if st.button('← Previous', disabled=(st.session_state.current_page == 1), use_container_width=True):
                    st.session_state.current_page -= 1
                    st.rerun()
            
            with pagination_cols[1]:
                st.markdown(f"<div style='text-align: center; padding: 10px;'>Page {st.session_state.current_page} of {total_pages}</div>", unsafe_allow_html=True)
            
            with pagination_cols[2]:
                if st.button('Next →', disabled=(st.session_state.current_page >= total_pages), use_container_width=True):
                    st.session_state.current_page += 1
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            # User portrait (replace with your actual portrait image)
            st.markdown("### 🧍 Your Current Fit")
            
            # Display selected item on portrait or default portrait
            if st.session_state.selected_item:
                st.image(st.session_state.selected_item['url'], use_container_width=True)
                st.caption(f"Selected: {st.session_state.selected_item['id']}")
            else:
                # Default portrait - replace with your actual user portrait URL
                portrait_url = 'user-portrait.jpeg' # "https://via.placeholder.com/400x600/E0BBE4/000000?text=Your+Portrait"
                st.image(portrait_url, use_container_width=True)
                st.caption("Select an item to preview")
                
    if st.button('Logout'): 
        st.session_state.authenticated = False
        st.session_state.page = 'login'
        st.session_state.USERNAME = None
        st.success('Successfully logged out.')

# NOTE: UNCOMMENT JUST IN CASE CLAUDE DOESN'T WORK OUT
# def selector_page():
#     if 'authenticated' in st.session_state and st.session_state.authenticated:
#         st.title("💃 Outfit Selector")

#         # Get image IDs from MongoDB based on clothing category and user
#         top_img_ids = mongodb_filter_by_user_and_category(st.session_state.USERNAME, 'top')
#         bottom_img_ids = mongodb_filter_by_user_and_category(st.session_state.USERNAME, 'bottom')

#         # Connect to S3 bucket
#         bucketname = os.environ['S3_BUCKET_NAME']
#         s3_resource = connect_s3('resource')
#         s3_client = connect_s3('client')
#         bucket = s3_resource.Bucket(bucketname)
        
#         # Filter out all keys from bucket under corresponding username
#         user_image_keys = [obj.key for obj in bucket.objects.filter(Prefix=st.session_state.USERNAME)]

#         def find_s3_key(img_id, keys):
#             for k in keys:
#                 if img_id in k:
#                     return k
#             return None

#         # Map IDs to S3 keys to filter according to main clothing123123 category
#         top_keys = [find_s3_key(id_, user_image_keys) for id_ in top_img_ids]
#         bottom_keys = [find_s3_key(id_, user_image_keys) for id_ in bottom_img_ids]

#         # Remove None values
#         top_keys = [k for k in top_keys if k]
#         bottom_keys = [k for k in bottom_keys if k]

#         def display_images(title, keys, client):
#             st.subheader(title)
#             # url_list=[]
#             if keys:
#                 for key in keys:
#                     url = client.generate_presigned_url(
#                         'get_object',
#                         Params={'Bucket': bucketname, 'Key': key},
#                         ExpiresIn=3600
#                     )
#                     # url_list.append(url)
#                     st.markdown(f"![t-shirt]({url})") 

#                     # st.image(url, caption=key.split('/')[-1], width='stretch')
#             else:
#                 st.info(f"No {title.lower()} found.")

#         display_images("👕 Tops", top_keys, s3_client)
#         display_images("👖 Bottoms", bottom_keys, s3_client)

#         st.image('user-portrait.jpeg')

        # Extract all image bytes for each category
        # outerwear_bytes = filter_image_data_by_category(st.session_state.USERNAME, 'outerwear')
        # topwear_bytes = filter_image_data_by_category(st.session_state.USERNAME, 'top')
        # bottomwear_bytes = filter_image_data_by_category(st.session_state.USERNAME, 'bottomwear')
        # footwear_bytes = filter_image_data_by_category(st.session_state.USERNAME, 'footwear')
        # accessories_bytes = filter_image_data_by_category(st.session_state.USERNAME, 'accessories')

        # # st.write(topwear_bytes)

        # # st.write(bottomwear_bytes)

        # # # Create selectors and store selected images
        # # selected_images = {}

        # # categories = [
        # #     # ("outerwear",   "Outerwear",   outerwear_bytes),
        # #     ("topwear",     "Top",         topwear_bytes),
        # #     ("bottomwear",  "Bottomwear",  bottomwear_bytes),
        # #     # ("footwear",    "Shoes",       footwear_bytes),
        # #     # ("accessories", "Accessories", accessories_bytes),
        # # ]
        
        # for key, label, img_bytes in categories:
        #     selected_img = create_image_selector(key, label, img_bytes, 300, 350, items_per_page=1)
        #     if selected_img:
        #         selected_images[key] = selected_img
        #     st.divider()
        
        # # Create outfit compilation button
        # if st.button("📸 Create Outfit & Send to WhatsApp", type="primary"):
        #     if len(selected_images) >= 2:  # At least 2 items selected
        #         outfit_grid = create_outfit_grid(selected_images)
                
        #         # Preview the grid
        #         st.image(outfit_grid, caption="Your Outfit Compilation")
                
        #         # TODO: Implement WhatsApp sending logic here
        #         # send_to_whatsapp(outfit_grid)
                
        #         st.success("Outfit compilation created! Ready to send to WhatsApp.")
        #     else:
        #         st.warning("Please select at least 2 items to create an outfit.")

        # for key, label, img_bytes in categories:
        #     if not img_bytes:
        #         st.write(f"No images to display for {label}")
        #         st.divider()
        #         continue

        #     items = [{"img": b64(b), "title": f"Image {i+1}", "text": ""} for i, b in enumerate(img_bytes)]
        #     st.write(f"Select a {label}")
        #     carousel(items, interval=None, indicators=True, controls=True, key=f"carousel_{key}")

        #     # hidden text input that JS will keep updated with the active index
        #     st.divider()
