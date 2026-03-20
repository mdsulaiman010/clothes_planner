import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_EXPIRATION_HOURS = 24

    # MongoDB
    MONGODB_ID = os.environ.get('MONGODB_ID')
    MONGODB_PW = os.environ.get('MONGODB_PW')
    MONGODB_CLUSTER = os.environ.get('MONGODB_LOOKBOOK_CLUSTER')

    # Supabase
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

    # AWS S3
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
    S3_BUCKET_REGION = os.environ.get('S3_BUCKET_REGION', 'ap-southeast-1')
    CREDENTIALS_DIR = os.environ.get('CREDENTIALS_DIR')

    # Gemini
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

    # Moondream
    MOONDREAM_ENDPOINT = os.environ.get('MOONDREAM_ENDPOINT')

    # Fashn.ai
    FASHN_API_KEY = os.environ.get('FASHN_API_KEY')

    # Paths
    PROMPTS_DIR = os.path.join(os.path.dirname(__file__), 'prompts')
    TEMP_DIR = os.path.join(os.path.dirname(__file__), 'tempImages')
