import uuid
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.dataset import Dataset, DatasetVersion, DatasetStatus
from src.datasets.repositories.dataset import dataset_repo, dataset_version_repo
from src.datasets.schemas.dataset import DatasetCreate
from src.datasets.storage.local import FileSystemStorage

class DatasetService:
    def __init__(self):
        # In production, this would be injected or configured via settings
        self.storage = FileSystemStorage()

    async def create_dataset(
        self, db: AsyncSession, *, organization_id: uuid.UUID, dataset_in: DatasetCreate
    ) -> Dataset:
        db_obj = Dataset(
            organization_id=organization_id,
            name=dataset_in.name,
            description=dataset_in.description,
            base_format=dataset_in.base_format,
            status=DatasetStatus.PENDING
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_upload_params(self, dataset_id: uuid.UUID) -> Tuple[str, str]:
        """
        Returns (upload_url, file_path)
        """
        file_path = f"datasets/{dataset_id}/raw/upload.jsonl"
        upload_url = await self.storage.get_presigned_url(file_path)
        return upload_url, file_path

    async def create_initial_version(
        self, db: AsyncSession, *, dataset_id: uuid.UUID, s3_uri: str
    ) -> DatasetVersion:
        db_obj = DatasetVersion(
            dataset_id=dataset_id,
            version_number=1,
            s3_uri=s3_uri,
            status=DatasetStatus.PROCESSING,
            metadata_info={"original_file": s3_uri}
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

dataset_service = DatasetService()
