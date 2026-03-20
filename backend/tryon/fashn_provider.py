import os
import requests
from tryon.base import TryOnProvider

FASHN_API_BASE = 'https://api.fashn.ai/v1'


class FashnAiProvider(TryOnProvider):
    def __init__(self):
        self.api_key = os.environ.get('FASHN_API_KEY', '')

    def _headers(self):
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

    def submit_job(self, selfie_image_b64: str, clothing_image_url: str) -> dict:
        resp = requests.post(
            f'{FASHN_API_BASE}/run',
            headers=self._headers(),
            json={
                'model_image': f'data:image/jpeg;base64,{selfie_image_b64}',
                'garment_image': clothing_image_url,
                'category': 'auto',
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            'job_id': data.get('id', ''),
            'status': data.get('status', 'processing'),
        }

    def get_result(self, job_id: str) -> dict:
        resp = requests.get(
            f'{FASHN_API_BASE}/status/{job_id}',
            headers=self._headers(),
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            'status': data.get('status', 'processing'),
            'result_image_url': data.get('output', [None])[0] if data.get('status') == 'completed' else None,
        }
