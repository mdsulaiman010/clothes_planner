import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))


class GeminiChatService:
    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
        self.model = 'gemini-2.5-flash'

    def get_reply(self, message: str, system_prompt: str, history: list[dict]) -> str:
        contents = []

        # Add conversation history
        for msg in history:
            role = 'user' if msg['role'] == 'user' else 'model'
            contents.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg['content'])],
            ))

        # Add current user message
        contents.append(types.Content(
            role='user',
            parts=[types.Part.from_text(text=message)],
        ))

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
            ),
        )

        return response.text
