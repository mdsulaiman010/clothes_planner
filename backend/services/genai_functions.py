import os
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from google import genai

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

def classify_image(image_bytes):
    # Read in classificaiton prompt
    prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
    with open(os.path.join(prompts_dir, 'classification_prompt1.txt'), 'r') as f:
        classification_prompt = f.read()

    # Initialize Gemini client and inject prompt + image
    client = genai.Client()
    
    image = Image.open(BytesIO(image_bytes))
    
    try:
        response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=[
                    classification_prompt,
                    image
                ]
            )
        
        return response.text
    except Exception as e:
        raise RuntimeError(f"Image classification failed: {e}") from e
