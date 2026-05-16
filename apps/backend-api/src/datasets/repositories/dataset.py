from typing import List, Optional, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.dataset import Dataset, DatasetVersion
from src.repositories.base import BaseRepository
from src.datasets.schemas.dataset import DatasetCreate, DatasetUpdate

class DatasetRepository(BaseRepository[Dataset, DatasetCreate, DatasetUpdate]):
    async def get_by_org(self, db: AsyncSession, organization_id: str) -> List[Dataset]:
        query = select(self.model).where(self.model.organization_id == organization_id)
        result = await db.execute(query)
        return result.scalars().all()

dataset_repo = DatasetRepository(Dataset)

class DatasetVersionRepository(BaseRepository[DatasetVersion, Any, Any]):
    async def get_latest_version(self, db: AsyncSession, dataset_id: str) -> Optional[DatasetVersion]:
        query = select(self.model).where(self.model.dataset_id == dataset_id).order_by(self.model.version_number.desc())
        result = await db.execute(query)
        return result.scalars().first()

dataset_version_repo = DatasetVersionRepository(DatasetVersion)
