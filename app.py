import streamlit as st
import sqlite3
import hashlib
from PIL import Image
import io, time, os
from pymongo import MongoClient
import gridfs
from db_functions import *
from datetime import datetime
from google import genai
from google.genai import types
from streamlit_carousel import carousel
from streamlit.components.v1 import html
import base64
from bs4 import BeautifulSoup

def b64(b): return "data:image/png;base64," + base64.b64encode(b).decode()

st.set_page_config(page_title="Mobile Image Uploader", page_icon="📷", layout="centered")
with open ('style.css', 'r') as f:
    css = f.read()
st.markdown(f"<style>{css}</style>",unsafe_allow_html=True)

def classify_image(image_bytes):
    # Initialize Google generative AI client
    client = genai.Client()

    # Pre-defined classification prompt
    classification_prompt = '''Categorize the attached clothing into 1 of 5 categories: outerwear, top, bottomwear, footwear, accessories. 
    
    Only return the predicted category. 
    
    Do not provide explanations or additional discussion points.
    '''

    # Predict with LLM
    response = client.models.generate_content(model='gemini-2.5-flash', contents=[types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg'), classification_prompt])
    return response.candidates[0].content.parts[0].text


def register_page():
    st.title('Registration Page')
    username = st.text_input('Username')
    password = st.text_input('Password', type='password')
    confirm_password = st.text_input('Confirm Password', type='password')

    if st.button('Register'):
        if username and password and password == confirm_password:
            register_user(username, password)
            st.success('Registration successful! Please login...')
            st.session_state.page = 'login'
        elif password != confirm_password:
            st.error('Passwords do not match. Please re-enter...')
        else:
            st.error('Please enter both username and password.')


def login_page():
    st.title('Login Page')
    username = st.text_input('Username')
    password = st.text_input('Password', type='password')

    if st.button('Login'):
        if authenticate(username, password):
            st.session_state.authenticated = True
            st.success('Login successful!')
            st.session_state.page = 'image_uploader'
        else:
            st.error('Invalid username or password')
            

def image_page():
    if 'authenticated' in st.session_state and st.session_state.authenticated:
        _, clothes_db, fs = connect_mongodb()
        st.title("📷 Mobile Image Uploader")

        # 1) Take a photo
        shot = st.camera_input("Take a photo")

        # 2) Or pick from gallery/files
        uploads = st.file_uploader(
            "Or choose from gallery",
            type=["png","jpg","jpeg","webp","gif"],
            accept_multiple_files=True
        )

        def save_bytes(name: str, raw: bytes, mime: str):
            # Classify image 
            img_category = classify_image(raw)

            img = Image.open(io.BytesIO(raw))
            _id = fs.put(
                raw,
                filename=name,
                contentType=mime or "application/octet-stream",
                metadata={
                    "width": img.width, "height": img.height,
                    "format": img.format, "bytes": len(raw),
                    "uploaded_at": time.time(),
                    'category': img_category
                },
            )
            st.success(f"Uploaded {name} to database → {_id}")

        if shot is not None:
            save_bytes(f"clothing_{datetime.now().strftime('%d%m%Y_%H%M')}.jpg", shot.getvalue(), "image/jpeg")

        if uploads:
            for upload in uploads:
                save_bytes(upload.name, upload.read(), upload.type)

    if st.button('Logout'):
        st.session_state.authenticated = False
        st.session_state.page = 'login'
        st.success('Successfully logged out.')

def b64(img_bytes):
    """Convert image bytes to base64 string"""
    return base64.b64encode(img_bytes).decode()


import streamlit as st
from PIL import Image
import io
import base64

def b64(img_bytes):
    """Convert image bytes to base64 string"""
    return base64.b64encode(img_bytes).decode()

def create_image_selector(key, label, img_bytes, card_width=200, card_height=250, items_per_page=4):
    """Create a custom image selector with carousel/sliding window navigation"""
    if not img_bytes:
        st.write(f"No images to display for {label}")
        return None
    
    # Initialize session state for this category if not exists
    if f"selected_{key}" not in st.session_state:
        st.session_state[f"selected_{key}"] = 0
    
    # Initialize carousel page state
    if f"carousel_page_{key}" not in st.session_state:
        st.session_state[f"carousel_page_{key}"] = 0
    
    num_images = len(img_bytes)
    total_pages = (num_images + items_per_page - 1) // items_per_page  # Ceiling division
    current_page = st.session_state[f"carousel_page_{key}"]
    
    st.write(f"Select a {label}")
    
    # Navigation controls
    nav_cols = st.columns([1, 3, 1])
    
    with nav_cols[0]:
        if st.button("◀ Previous", key=f"prev_{key}", disabled=(current_page == 0),
                    width='content'):
            st.session_state[f"carousel_page_{key}"] = max(0, current_page - 1)
            st.rerun()
    
    with nav_cols[1]:
        st.markdown(f"<div style='text-align: center; padding: 8px;'>Page {current_page + 1} of {total_pages} ({num_images} items)</div>", 
                   unsafe_allow_html=True)
    
    with nav_cols[2]:
        if st.button("Next ▶", key=f"next_{key}", disabled=(current_page >= total_pages - 1),
                    width='content'):
            st.session_state[f"carousel_page_{key}"] = min(total_pages - 1, current_page + 1)
            st.rerun()
    
    st.markdown("---")
    
    # Calculate visible images for current page
    start_idx = current_page * items_per_page
    end_idx = min(start_idx + items_per_page, num_images)
    
    # Display images in columns for current page
    cols = st.columns(items_per_page)
    
    for col_idx, img_idx in enumerate(range(start_idx, end_idx)):
        with cols[col_idx]:
            # Load and resize image to standard dimensions
            img = Image.open(io.BytesIO(img_bytes[img_idx]))
            
            # Resize image to fit card while maintaining aspect ratio
            img.thumbnail((card_width, card_height), Image.Resampling.LANCZOS)
            
            # Create a new image with fixed dimensions and center the resized image
            standardized_img = Image.new('RGB', (card_width, card_height), color='white')
            offset = ((card_width - img.width) // 2, (card_height - img.height) // 2)
            standardized_img.paste(img, offset)
            
            # Display standardized image
            st.image(standardized_img, width='content')
            
            # Selection button
            is_selected = st.session_state[f"selected_{key}"] == img_idx
            button_label = "✓ Selected" if is_selected else "Select"
            
            if st.button(button_label, key=f"btn_{key}_{img_idx}", type="primary" if is_selected else "secondary", width='content'):
                st.session_state[f"selected_{key}"] = img_idx
                st.rerun()
    
    # Fill empty columns if on last page
    for col_idx in range(end_idx - start_idx, items_per_page):
        with cols[col_idx]:
            st.empty()
    
    return img_bytes[st.session_state[f"selected_{key}"]]

def create_outfit_grid(selected_images):
    # Define the 2x2 grid layout (adjust based on your preference)
    grid_positions = {
        'outerwear': (0, 0),
        'topwear': (0, 1),
        'bottomwear': (1, 0),
        'footwear': (1, 1),
    }
    
    # Create base image (2x2 grid)
    img_size = 300  # Size of each cell
    grid_img = Image.new('RGB', (img_size * 2, img_size * 2), color='white')
    
    for key, img_bytes in selected_images.items():
        if img_bytes and key in grid_positions:
            row, col = grid_positions[key]
            img = Image.open(io.BytesIO(img_bytes))
            img = img.resize((img_size, img_size), Image.Resampling.LANCZOS)
            grid_img.paste(img, (col * img_size, row * img_size))
    
    # Convert to bytes
    buf = io.BytesIO()
    grid_img.save(buf, format='PNG')
    buf.seek(0)
    return buf.getvalue()


def selector_page():
    if 'authenticated' in st.session_state and st.session_state.authenticated:
        st.title("💃 Outfit Selector")

        # Extract all image bytes for each category
        outerwear_bytes = filter_image_data_by_category('outerwear')
        topwear_bytes = filter_image_data_by_category('top')
        bottomwear_bytes = filter_image_data_by_category('bottomwear')
        footwear_bytes = filter_image_data_by_category('footwear')
        accessories_bytes = filter_image_data_by_category('accessories')

        # Create selectors and store selected images
        selected_images = {}

        categories = [
            ("outerwear",   "Outerwear",   outerwear_bytes),
            ("topwear",     "Top",         topwear_bytes),
            ("bottomwear",  "Bottomwear",  bottomwear_bytes),
            ("footwear",    "Shoes",       footwear_bytes),
            ("accessories", "Accessories", accessories_bytes),
        ]
        
        for key, label, img_bytes in categories:
            selected_img = create_image_selector(key, label, img_bytes, 300, 350, items_per_page=1)
            if selected_img:
                selected_images[key] = selected_img
            st.divider()
        
        # Create outfit compilation button
        if st.button("📸 Create Outfit & Send to WhatsApp", type="primary"):
            if len(selected_images) >= 2:  # At least 2 items selected
                outfit_grid = create_outfit_grid(selected_images)
                
                # Preview the grid
                st.image(outfit_grid, caption="Your Outfit Compilation")
                
                # TODO: Implement WhatsApp sending logic here
                # send_to_whatsapp(outfit_grid)
                
                st.success("Outfit compilation created! Ready to send to WhatsApp.")
            else:
                st.warning("Please select at least 2 items to create an outfit.")



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

    if st.button('Logout'): 
        st.session_state.authenticated = False
        st.session_state.page = 'login'
        st.success('Successfully logged out.')

def main():
    connect_db()

    # Initialize user state as "NOT AUTHENTICATED" to maintain user login status
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.page = 'login'

    if 'authenticated' in st.session_state and st.session_state.authenticated:
        page = st.sidebar.selectbox('Select a page', ['Image Upload', 'Clothes Selector', 'Logout'])
        if page == 'Image Upload':
            st.session_state.page = 'image_uploader'
        
        if page == 'Clothes Selector':
            st.session_state.page = 'selector'
    
        if page == 'Logout':
            st.session_state.page = 'login'
            st.session_state.authenticated = False

    else:
        page = st.sidebar.selectbox('Select a page', ['Login', 'Register'])
        if page == 'Login':
            st.session_state.page = 'login'
        if page == 'Register':
            st.session_state.page = 'register'

    # Page switchboard
    if st.session_state.page == 'login':
        login_page()
    elif st.session_state.page == 'register':
        register_page()
    elif st.session_state.page == 'image_uploader':
        image_page()
    elif st.session_state.page == 'selector':
        selector_page()

if __name__ == "__main__":
    main()


















