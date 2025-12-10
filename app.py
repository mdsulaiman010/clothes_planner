import streamlit as st
from streamlit.components.v1 import html
from streamlit_page_functions import *

st.set_page_config(page_title="Mobile Image Uploader", page_icon="📷", layout="centered")
with open ('style.css', 'r') as f:
    css = f.read()
st.markdown(f"<style>{css}</style>",unsafe_allow_html=True)

def main():
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


















