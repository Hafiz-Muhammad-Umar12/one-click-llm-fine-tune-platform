import os
from typing import BinaryIO
from src.datasets.storage.local import FileSystemStorage

class ArtifactStorageService(FileSystemStorage):
    """
    Handles storage of Model Artifacts (Weights, LoRA Adapters).
    Extends the base FileSystemStorage for local dev, but in production
    this would be backed by S3 with presigned URL generation for vLLM pods.
    """
    def __init__(self, base_path: str = "/tmp/ai_artifacts"):
        super().__init__(base_path=base_path)

    async def get_secure_download_url(self, artifact_path: str, expiration: int = 3600) -> str:
        """
        Generates a secure signed URL for the inference pod to download weights.
        In local dev, we just return the local file path.
        """
        # Production: return s3_client.generate_presigned_url('get_object', ...)
        return f"file://{os.path.join(self.base_path, artifact_path)}"

artifact_storage = ArtifactStorageService()
