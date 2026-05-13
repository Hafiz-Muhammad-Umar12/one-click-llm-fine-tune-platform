import os
import aiofiles
from typing import BinaryIO
from src.datasets.storage.base import BaseStorage

class FileSystemStorage(BaseStorage):
    def __init__(self, base_path: str = "/tmp/storage"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    async def upload_file(self, file_path: str, content: BinaryIO) -> str:
        full_path = os.path.join(self.base_path, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        async with aiofiles.open(full_path, mode='wb') as f:
            await f.write(content.read())
        return full_path

    async def download_file(self, file_path: str) -> BinaryIO:
        full_path = os.path.join(self.base_path, file_path)
        return open(full_path, 'rb')

    async def delete_file(self, file_path: str) -> bool:
        full_path = os.path.join(self.base_path, file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False

    async def get_presigned_url(self, file_path: str, expiration: int = 3600) -> str:
        # Mock URL for local development
        return f"file://{os.path.join(self.base_path, file_path)}"
