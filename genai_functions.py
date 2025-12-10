from google import genai
from google.genai import types
import json

def classify_image(image_bytes):
    # Initialize Google generative AI client
    client = genai.Client()

    # Read in listed categories for clothes labelling
    with open('prompts/clothing_hierarchy.json', 'r') as categories_f:
        fashion_taxonomy = str(json.load(categories_f))
    
    with open('prompts/classifier_sys_prompt.txt', 'r') as f:
        classification_prompt = f.read()

        # Substitute the fashion taxonomy into prompt template
        classification_prompt = classification_prompt.replace('{{clothes_json}}', fashion_taxonomy)

    # Predict with LLM
    response = client.models.generate_content(model='gemini-2.5-flash', contents=[types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg'), classification_prompt])
    return response.candidates[0].content.parts[0].text