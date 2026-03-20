import hashlib
import time
import os
import io
import json
from pymongo import MongoClient
from supabase import create_client
from PIL import Image
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

max_retries = 5

################################################################################
#####     MongoDB Functions (store details on uploaded images by user)     #####
################################################################################


def connect_mongodb():
    MONGO_ID = os.environ['MONGODB_ID']
    MONGO_PW = os.environ['MONGODB_PW']
    MONGO_URI = os.environ['MONGODB_LOOKBOOK_CLUSTER']
    MONGO_URI = MONGO_URI.replace('<user_id>', MONGO_ID).replace('<user_pw>', MONGO_PW)

    for i in range(max_retries):
        try:
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
    client, db = connect_mongodb()
    collection = db['items']
    query = {'uploadedBy': username, 'mainCategory': category}
    filtered_img_details = collection.find(query).skip(skip).limit(limit)
    return [str(doc["_id"]) for doc in filtered_img_details]


def mongodb_count_by_user_and_category(username, category):
    client, db = connect_mongodb()
    collection = db['items']
    query = {'uploadedBy': username, 'mainCategory': category}
    return collection.count_documents(query)


def mongodb_get_item_by_id(item_id):
    from bson import ObjectId
    client, db = connect_mongodb()
    collection = db['items']
    return collection.find_one({'_id': ObjectId(item_id)})


def mongodb_delete_item(item_id):
    from bson import ObjectId
    client, db = connect_mongodb()
    collection = db['items']
    result = collection.delete_one({'_id': ObjectId(item_id)})
    return result.deleted_count > 0


def mongodb_save_image_and_metadata(collection, username, raw):
    from services.genai_functions import classify_image

    prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
    with open(os.path.join(prompts_dir, 'clothing_hierarchy.json'), 'r') as categories_f:
        fashion_taxonomy = json.load(categories_f)

    subCategory = classify_image(raw)
    mainCategory = [key for key, value in fashion_taxonomy.items() if subCategory in value]
    mainCategory = mainCategory[0] if mainCategory else 'accessories'

    converted_metadata_dict = {}

    img = Image.open(io.BytesIO(raw))
    img_format = img.format or 'PNG'
    ext = img_format.lower()
    img = convert_img_to_square(img, 256)

    converted_metadata_dict['mainCategory'] = mainCategory
    converted_metadata_dict['subCategory'] = subCategory
    converted_metadata_dict['width'] = img.width
    converted_metadata_dict['height'] = img.height
    converted_metadata_dict['format'] = img_format
    converted_metadata_dict['bytes'] = len(raw)
    converted_metadata_dict['uploadedBy'] = username
    converted_metadata_dict['uploadedAt'] = time.time()

    temp_dir = os.path.join(os.path.dirname(__file__), '..', 'tempImages')
    os.makedirs(temp_dir, exist_ok=True)

    for i in range(max_retries):
        try:
            result = collection.insert_one(converted_metadata_dict)
            item_id = result.inserted_id

            filepath = f"{item_id}_{username}.{ext}"
            with open(os.path.join(temp_dir, filepath), "wb") as f:
                f.write(raw)

            return str(item_id), filepath
        except Exception as e:
            if i < max_retries - 1:
                print(f'[Attempt {i+1}] Failed to insert into MongoDB: {e}. Retrying...')
                time.sleep(5)
            else:
                print('Max image upload attempts reached.')
                return None, None


######################################
#####     Supabase Functions     #####
######################################


def connect_supabase():
    SUPABASE_URL = os.environ['SUPABASE_URL']
    SUPABASE_KEY = os.environ['SUPABASE_KEY']
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return client


def supabase_check_existing_users(client):
    response = client.table('users').select('username').execute()
    return [item['username'] for item in response.data]


def supabase_add_new_user(client, username, password, phone_number):
    existing_users = supabase_check_existing_users(client)

    if any(user for user in existing_users if user == username):
        return False

    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    user_dict = {
        'username': username,
        'password': hashed_pw,
        'mobile_number': phone_number,
    }
    response = client.table('users').insert(user_dict).execute()
    return bool(response.data)


def supabase_authenticate(username, password):
    client = connect_supabase()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    response = client.table('users').select('*').eq('username', username).eq('password', hashed_pw).execute()
    return len(response.data) > 0


######################################
#####     Utility Functions      #####
######################################


def convert_img_to_square(image: Image.Image, square_size, fill_color=(255, 255, 255)):
    width, height = image.size
    max_side = max(width, height)

    square_img = Image.new(image.mode, (max_side, max_side), fill_color)
    paste_x = (max_side - width) // 2
    paste_y = (max_side - height) // 2
    square_img.paste(image, (paste_x, paste_y))

    return square_img.resize((square_size, square_size), Image.LANCZOS)
