import streamlit as st
from PIL import Image
import io, time, os
from pymongo import MongoClient
import gridfs

st.set_page_config(page_title="Mobile Image Uploader", page_icon="📷", layout="centered")

# --- Mongo ---
# client = MongoClient(st.secrets["mongo"]["uri"])
# db = client[st.secrets["mongo"]["db"]]
# fs = gridfs.GridFS(db)

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
    st.success(f"Uploaded {name}")

if shot is not None:
    save_bytes("camera.jpg", shot.getvalue(), "image/jpeg")

if uploads:
    for up in uploads:
        save_bytes(up.name, up.read(), up.type)

st.divider()
st.subheader("Latest")
