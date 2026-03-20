import uuid
from tryon.base import TryOnProvider


class LocalProvider(TryOnProvider):
    """Stub for future lightweight local try-on (PIL overlay)."""

    def submit_job(self, selfie_image_b64: str, clothing_image_url: str) -> dict:
        return {
            'job_id': str(uuid.uuid4()),
            'status': 'not_implemented',
        }

    def get_result(self, job_id: str) -> dict:
        return {
            'status': 'not_implemented',
            'result_image_url': None,
        }
