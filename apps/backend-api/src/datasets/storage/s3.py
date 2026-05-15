import aioboto3
from typing import BinaryIO, Optional
from src.datasets.storage.base import BaseStorage

class S3Storage(BaseStorage):
    def __init__(
        self, 
        bucket_name: str,
        endpoint_url: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        region_name: str = "us-east-1"
    ):
        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url
        self.access_key = access_key
        self.secret_key = secret_key
        self.region_name = region_name
        self.session = aioboto3.Session()

    async def upload_file(self, file_path: str, content: BinaryIO) -> str:
        async with self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region_name
        ) as s3:
            await s3.put_object(Bucket=self.bucket_name, Key=file_path, Body=content.read())
            return f"s3://{self.bucket_name}/{file_path}"

    async def download_file(self, file_path: str) -> BinaryIO:
        async with self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region_name
        ) as s3:
            response = await s3.get_object(Bucket=self.bucket_name, Key=file_path)
            return response["Body"]

    async def delete_file(self, file_path: str) -> bool:
        async with self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region_name
        ) as s3:
            await s3.delete_object(Bucket=self.bucket_name, Key=file_path)
            return True

    async def get_presigned_url(self, file_path: str, expiration: int = 3600) -> str:
        async with self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region_name
        ) as s3:
            url = await s3.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": self.bucket_name, "Key": file_path},
                ExpiresIn=expiration
            )
            return url
