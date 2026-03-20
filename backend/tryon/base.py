from abc import ABC, abstractmethod


class TryOnProvider(ABC):
    @abstractmethod
    def submit_job(self, selfie_image_b64: str, clothing_image_url: str) -> dict:
        """Submit a try-on job. Returns {'job_id': str, 'status': str}."""
        pass

    @abstractmethod
    def get_result(self, job_id: str) -> dict:
        """Get job result. Returns {'status': str, 'result_image_url': str | None}."""
        pass
