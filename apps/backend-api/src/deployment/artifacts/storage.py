import os
import logging
from typing import BinaryIO, Optional
from src.core.config import settings
from src.datasets.storage.local import FileSystemStorage
from src.datasets.storage.s3 import S3Storage

logger = logging.getLogger(__name__)

def get_storage_client():
    if settings.STORAGE_BACKEND == "s3":
        logger.info(f"Initializing S3 Storage Backend (Bucket: {settings.S3_BUCKET})")
        return S3Storage(
            bucket_name=settings.S3_BUCKET,
            endpoint_url=settings.S3_ENDPOINT_URL,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION
        )
    else:
        logger.info(f"Initializing Local FileSystem Storage Backend (Path: {settings.STORAGE_BASE_PATH})")
        return FileSystemStorage(base_path=settings.STORAGE_BASE_PATH)

class ArtifactStorageService:
    """
    Handles storage of Model Artifacts (Weights, LoRA Adapters).
    Uses an underlying storage client (Local or S3).
    """
    def __init__(self):
        self.client = get_storage_client()

    async def upload_artifact(self, artifact_path: str, content: BinaryIO) -> str:
        return await self.client.upload_file(artifact_path, content)

    async def get_secure_download_url(self, artifact_path: str, expiration: int = 3600) -> str:
        """
        Generates a secure signed URL for the inference pod to download weights.
        """
        return await self.client.get_presigned_url(artifact_path, expiration=expiration)

    async def delete_artifact(self, artifact_path: str) -> bool:
        return await self.client.delete_file(artifact_path)

artifact_storage = ArtifactStorageService()
