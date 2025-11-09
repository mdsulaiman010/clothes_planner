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
import base64

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


def selector_page():
    if 'authenticated' in st.session_state and st.session_state.authenticated:
        st.title("💃 Outfit Selector")

        # Extract all image bytes for each category
        outerwear_bytes = filter_image_data_by_category('outerwear')
        topwear_bytes = filter_image_data_by_category('top')
        bottomwear_bytes = filter_image_data_by_category('bottomwear')
        footwear_bytes = filter_image_data_by_category('footwear')
        accessories_bytes = filter_image_data_by_category('accessories')

        for segment, img_bytes in zip(['Outerwear', 'Top', 'Bottomwear', 'Shoes', 'Accessories'], [outerwear_bytes, topwear_bytes, bottomwear_bytes, footwear_bytes, accessories_bytes]):
            if len(img_bytes) == 0:
                print(f'No images to display for {segment}')
            
            else:
                images = [{"img": b64(b), "title": f"Image {i+1}", "text": ""} for i,b in enumerate(img_bytes)]
                
                st.write(f'Select an {segment}')
                carousel(images, interval=None)
                st.divider()

                
        # # Create image carousel for each category
        # outerwear_images = [{"img": b64(b), "title": f"Image {i+1}", "text": ""} for i,b in enumerate(outerwear_bytes)]
        # topwear_images = [{"img": b64(b), "title": f"Image {i+1}", "text": ""} for i,b in enumerate(topwear_bytes)]
        # bottomwear_images = [{"img": b64(b), "title": f"Image {i+1}", "text": ""} for i,b in enumerate(bottomwear_bytes)]
        # footwear_images = [{"img": b64(b), "title": f"Image {i+1}", "text": ""} for i,b in enumerate(footwear_bytes)]
        # # accessories_images = [{"img": b64(b), "title": f"Image {i+1}", "text": ""} for i,b in enumerate(accessories_bytes)]

        # for segment, images in zip(['Outerwear', 'Top', 'Bottomwear', 'Shoes'], [outerwear_images, topwear_images, bottomwear_images, footwear_images]):
        #     st.write(f'Select an {segment}')
        #     carousel(images)
        #     st.divider()


        # st.write('Outerwear')
        # carousel(topwear_images)
        # carousel(bottomwear_images)
        # carousel(footwear_images)
        # carousel(accessories_images)


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


















