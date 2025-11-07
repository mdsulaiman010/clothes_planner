import streamlit as st
import sqlite3
import hashlib
from PIL import Image
import io, time, os
from pymongo import MongoClient
import gridfs
from db_functions import *
from datetime import datetime

st.set_page_config(page_title="Mobile Image Uploader", page_icon="📷", layout="centered")

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
            img = Image.open(io.BytesIO(raw))
            _id = fs.put(
                raw,
                filename=name,
                contentType=mime or "application/octet-stream",
                metadata={
                    "width": img.width, "height": img.height,
                    "format": img.format, "bytes": len(raw),
                    "uploaded_at": time.time(),
                },
            )
            st.success(f"Uploaded {name} to database → {_id}")

        if shot is not None:
            save_bytes(f"clothing_{datetime.now().strftime('%d%m%Y_%H%M')}.jpg", shot.getvalue(), "image/jpeg")

        if uploads:
            for up in uploads:
                save_bytes(up.name, up.read(), up.type)

        st.divider()
        st.subheader("Latest")
        for f in clothes_db["fs.files"].find().sort("uploadDate", -1).limit(6):
            st.image(fs.get(f["_id"]).read(), caption=f.get("filename"), use_container_width=True)

        if st.button('Logout'):
            st.session_state.authenticated = False
            st.session_state.page = 'login'
            st.success('Successfully logged out.')


def selector_page():
    if 'authenticated' in st.session_state and st.session_state.authenticated:
        st.title("💃 Outfit Selector")

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
            st.success('You have successfully logged out!')

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


















