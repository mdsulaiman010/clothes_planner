import hashlib
import sqlite3
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import gridfs
import io

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


def authenticate(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?",
              (username, hashed_pw))

    user = c.fetchone()
    conn.close()

    return True if user else False


#####################################
#####     MongoDB Functions     #####
#####################################

def connect_mongodb():
    # Load in relevant environment variables
    load_dotenv()
    MONGO_ID = os.environ['MONGODB_ID']
    MONGO_PW = os.environ['MONGODB_PW']
    MONGO_URI = os.environ['MONGODB_LOOKBOOK_CLUSTER']
    MONGO_URI = MONGO_URI.replace('<user_id>', MONGO_ID).replace('<user_pw>', MONGO_PW)

    try:
        # Define MongoDB client
        client = MongoClient(MONGO_URI)
        db = client['clothes']
        fs = gridfs.GridFS(db, collection="images")
        
        return client, db, fs

    except Exception as e:
        print(f'Error initializing DB. Error:\n{e}')
        return None, None, None
    
def filter_image_data_by_category(category):
    # Connect to MongoDB cluster
    client, db, fs = connect_mongodb()

    # Filter documents from files collection by category
    filtered_img_details = db['images.files'].find({'metadata.category': category})

    # Extract all relevant IDs for each image details
    file_ids = [details['_id'] for details in filtered_img_details]

    # Filter all documents in chunks collection based on filtered file IDs
    chunks = db['images.chunks'].find({'files_id': {'$in': file_ids}})
    chunks = list(chunks)

    if len(chunks) == 0:
        print('No images found for category')
        return []
    
    # Extract all image data as list of bytes
    images_data = [chunk['data'] for chunk in chunks]

    return images_data