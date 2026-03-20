import os
import moondream as md
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

MOONDREAM_ENDPOINT = os.environ.get('MOONDREAM_ENDPOINT', '')


def classify_image(image_bytes):
    prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
    with open(os.path.join(prompts_dir, 'classification_prompt1.txt'), 'r') as f:
        classification_prompt = f.read()

    model = md.vl(endpoint=MOONDREAM_ENDPOINT)
    image = Image.open(BytesIO(image_bytes))
    response = model.query(image, classification_prompt)

    return response['answer']
