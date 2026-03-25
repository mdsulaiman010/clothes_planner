import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = 'dev-secret-key-change-in-production'
    JWT_EXPIRATION_HOURS: int = 24

    # MongoDB
    MONGODB_ID: str = ''
    MONGODB_PW: str = ''
    MONGODB_LOOKBOOK_CLUSTER: str = ''

    # Supabase
    SUPABASE_URL: str = ''
    SUPABASE_KEY: str = ''

    # AWS S3
    S3_BUCKET_NAME: str = ''
    S3_BUCKET_REGION: str = 'ap-southeast-1'
    S3_CLIENT_ID: str = ''
    S3_SECRET_KEY: str = ''
    CREDENTIALS_DIR: str = ''

    # Gemini
    GEMINI_API_KEY: str = ''

    # Moondream
    MOONDREAM_ENDPOINT: str = ''

    # Fashn.ai
    FASHN_API_KEY: str = ''

    # Paths
    PROMPTS_DIR: str = os.path.join(os.path.dirname(__file__), 'prompts')
    TEMP_DIR: str = os.environ.get('TEMP_DIR', os.path.join(os.path.dirname(__file__), 'tempImages'))

    model_config = {
        'env_file': os.path.join(os.path.dirname(__file__), '..', '.env'),
        'extra': 'ignore',
    }


settings = Settings()
