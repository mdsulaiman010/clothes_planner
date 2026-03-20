import hashlib
import sqlite3
from pymongo import MongoClient
from supabase import create_client
import boto3
import os
import streamlit as st
from dotenv import load_dotenv
import pandas as pd
import time
import io
from PIL import Image
import re
import json
import ast
from genai_functions import classify_image

max_retries = 5
download_dir = os.environ['DOWNLOAD_DIR']

################################################################################
#####     MongoDB Functions (store details on uploaded images by user)     #####
################################################################################

def connect_mongodb():
    # Load in relevant environment variables
    load_dotenv()
    MONGO_ID = os.environ['MONGODB_ID']
    MONGO_PW = os.environ['MONGODB_PW']
    MONGO_URI = os.environ['MONGODB_LOOKBOOK_CLUSTER']
    MONGO_URI = MONGO_URI.replace('<user_id>', MONGO_ID).replace('<user_pw>', MONGO_PW)

    for i in range(max_retries):
        try:
            # Define MongoDB client
            client = MongoClient(MONGO_URI)
            db = client['clothes']
            return client, db

        except Exception as e:
            if i < max_retries - 1:
                print(f'[Attempt {i+1}] Failed to connect to MongoDB client. Retrying...')
                time.sleep(5)
            else:
                print(f'Error initializing DB. Error:\n{e}')
                return None, None
    
def mongodb_filter_by_user_and_category(username, category, skip=0, limit=20):
    # Connect to MongoDB cluster
    client, db = connect_mongodb()
    collection = db['items']

    # Filter documents from files collection by category
    query = {'uploadedBy': username, 'mainCategory': category}
    filtered_img_details = collection.find(query).skip(skip).limit(limit)
    return [str(doc["_id"]) for doc in filtered_img_details]

def mongodb_save_image_and_metadata(collection, username, raw):
    # Load in clothing hierarchy JSON contents as dictionary
    with open('prompts/clothing_hierarchy.json', 'r') as categories_f:
        fashion_taxonomy = json.load(categories_f)

    # Classify image 
    subCategory = classify_image(raw)
    mainCategory = [key for key, value in fashion_taxonomy.items() if subCategory in value][0]

    # Initialize document to store in MongoDB
    converted_metadata_dict = {} # ast.literal_eval(metadata_dict)
    
    # Read in image
    img = Image.open(io.BytesIO(raw))
    img_format = img.format or 'PNG'  # fallback if unknown
    ext = img_format.lower()
    img = convert_img_to_square(img, 256)

    # Store additional metadata for document
    converted_metadata_dict['mainCategory'] = mainCategory
    converted_metadata_dict['subCategory'] = subCategory
    converted_metadata_dict['width'] = img.width
    converted_metadata_dict['height'] = img.height
    converted_metadata_dict['format'] = img_format
    converted_metadata_dict['bytes'] = len(raw)
    converted_metadata_dict['uploadedBy'] = username
    converted_metadata_dict['uploadedAt'] = time.time()
    
    temp_dir = 'tempImages'
    os.makedirs(temp_dir, exist_ok=True)

    # Upload document to MongoDB and get corresponding item ID
    for i in range(max_retries):
        try:
            result = collection.insert_one(converted_metadata_dict)
            item_id =  result.inserted_id

            filepath = f"{item_id}_{username}.{ext}"
            with open(os.path.join('tempImages', filepath), "wb") as f:
                f.write(raw)

            return str(item_id), filepath
        
        except Exception as e:
            if i < max_retries - 1:
                print(f'[Attempt {i+1}] Failed to insert into MongoDB: {e}. Retrying...')
                time.sleep(5)
            else:
                print('Max image upload attempts reached.')
                return None, None
            
# NOTE: IMPLEMENT A DELETE ITEM FUNCTION FOR MONGODB

# def filter_image_data_by_category(username, category):
#     # Connect to MongoDB cluster
#     client, db, fs = connect_mongodb()

#     # Filter documents from files collection by category
#     filtered_img_details = db['images.files'].find({'metadata.uploadedBy': username, 'metadata.mainCategory': category})

#     # Extract all relevant IDs for each image details
#     file_ids = [details['_id'] for details in filtered_img_details]

#     # Filter all documents in chunks collection based on filtered file IDs
#     chunks = db['images.chunks'].find({'files_id': {'$in': file_ids}})
#     chunks = list(chunks)

#     if len(chunks) == 0:
#         print('No images found for category')
#         return []
    
#     # Extract all image data as list of bytes
#     images_data = [chunk['data'] for chunk in chunks]

#     return images_data

#################################################################
#####     AWS Functions (store uploaded images by user)     #####
#################################################################

def connect_s3(return_type='client', region_name='ap-southeast-1'):
    # Load in credentials file
    credentials_dir = os.environ['CREDENTIALS_DIR']
    credentials = pd.read_excel(credentials_dir)

    # Extract relevant credentials to instantiate S3 client
    AWS_ACCESS_KEY_ID = credentials.loc[credentials['application'] == 'aws_access_key', 'username'].values[0]
    AWS_SECRET_ACCESS_KEY = credentials.loc[credentials['application'] == 'aws_secret_key', 'username'].values[0]

    if return_type == 'client':
        for i in range(max_retries):
            try:
                s3_client = boto3.client(
                    service_name='s3',
                    aws_access_key_id=AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                    region_name=region_name
                )
                return s3_client

            except Exception as e:
                if i < max_retries - 1:
                    print(f'[Attempt {i+1}] Failed to connect to AWS S3. Retrying...')
                    time.sleep(5)
                else:
                    print(f'Max attempts reached, error connecting to AWS S3. Error:\n{e}')
                    return None
    
    elif return_type == 'resource':
        for i in range(max_retries):
            try:
                s3_resource = boto3.resource(
                    's3',
                    aws_access_key_id=AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                    region_name=region_name
                )
                return s3_resource
            except Exception as e:
                if i < max_retries - 1:
                    print(f'[Attempt {i+1}] Failed to create S3 resource. Retrying...')
                    time.sleep(5)
                else:
                    print(f'Max attempts reached, error creating S3 resource. Error:\n{e}')
                    return None
    else:
        raise ValueError("return_type must be 'client' or 'resource'")

def s3_upload_image_and_notify(item_path, username):
    s3_client = connect_s3(return_type='client')
    bucket_name = os.environ['S3_BUCKET_NAME'] # 'digi-closet-images'
    s3_key = f"{username}/{item_path}"

    for i in range(max_retries):
        try:
            s3_client.upload_file(Filename=os.path.join('tempImages', item_path), Bucket=bucket_name, Key=s3_key)
            print('Successfully uplaoded to AWS S3.')
            return True

        except Exception as e:
            if i < max_retries - 1:
                print(f'[Attempt {i+1}] Image upload failed. Retrying...')
            else:
                print('Max S3 upload attempts reached.')
                raise e
            
# NOTE: IMPLEMENT A DELETE ITEM FUNCTION FOR AWS S3

######################################
#####     Supabase Functions     #####
######################################

def connect_supabase():
    load_dotenv()

    SUPABASE_URL = os.environ['SUPABASE_URL']
    SUPABASE_KEY = os.environ['SUPABASE_KEY']

    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return client

def supabase_check_existing_users(client):
    response = client.table('users').select('username').execute()
    existing_users = [item['username'] for item in response.data]

    return existing_users

def supabase_add_new_user(client, username, password, phone_number):
    # Gather list of existing users in database
    existing_users = supabase_check_existing_users(client)

    # Verify if new user is creating new account with existing username in database
    if any(user for user in existing_users if user == username):
        print('Username already taken. Please try another one.')
        return False

    else:
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        user_dict = {'username': username, 
                     'password': hashed_pw,
                     'mobile_number': phone_number}

        response = client.table('users').insert(user_dict).execute()

        if response.data:
            print('Your account has been successfully created.')
            return True
        
def supabase_authenticate(username, password):
    client = connect_supabase()
    
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()

    response = client.table('users').select('*').eq('username', username).eq('password', hashed_pw).execute()
    return len(response.data) > 0





####################################
#####     SQLite Functions     #####
####################################

def connect_db():
    # Open and connect to database to run SQL
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Initialize users.db with 3 columns if doesn't exist 
    c.execute('''CREATE TABLE IF NOT EXISTS users
              (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
    
    # Disconnect from database
    conn.commit()
    conn.close()


def register_user(username, password):
    # Open and connect to database to run SQL
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Encode password, add username and hashed password to DB
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
              (username, hashed_pw))
    
    # Disconnect from database
    conn.commit()
    conn.close()


# def authenticate(username, password):
#     conn = sqlite3.connect('users.db')
#     c = conn.cursor()

#     hashed_pw = hashlib.sha256(password.encode()).hexdigest()
#     c.execute("SELECT * FROM users WHERE username = ? AND password = ?",
#               (username, hashed_pw))

#     user = c.fetchone()
#     conn.close()

#     return True if user else False

def convert_img_to_square(image: Image.Image, square_size, fill_color=(255, 255, 255)):
    """
    Converts an image to a 128x128 square by padding and resizing.
    """
    width, height = image.size
    max_side = max(width, height)

    # Pad to square
    square_img = Image.new(image.mode, (max_side, max_side), fill_color)
    paste_x = (max_side - width) // 2
    paste_y = (max_side - height) // 2
    square_img.paste(image, (paste_x, paste_y))

    # Resize to desired square size
    return square_img.resize((square_size, square_size), Image.LANCZOS)