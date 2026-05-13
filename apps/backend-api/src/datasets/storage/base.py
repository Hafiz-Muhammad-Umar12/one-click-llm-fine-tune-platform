from abc import ABC, abstractmethod
from typing import BinaryIO, Optional

class BaseStorage(ABC):
    @abstractmethod
    async def upload_file(self, file_path: str, content: BinaryIO) -> str:
        """Uploads a file and returns the URI/path."""
        pass

    @abstractmethod
    async def download_file(self, file_path: str) -> BinaryIO:
        """Downloads a file and returns the content stream."""
        pass

    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """Deletes a file."""
        pass

    @abstractmethod
    async def get_presigned_url(self, file_path: str, expiration: int = 3600) -> str:
        """Generates a presigned URL for direct upload/download."""
        pass
