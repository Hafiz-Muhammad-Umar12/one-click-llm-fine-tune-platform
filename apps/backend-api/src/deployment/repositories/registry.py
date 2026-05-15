from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.deployment import RegisteredModel, ModelVersion, ModelArtifact
from src.repositories.base import BaseRepository

class RegisteredModelRepository(BaseRepository[RegisteredModel, Any, Any]):
    async def get_by_org(self, db: AsyncSession, organization_id: str) -> List[RegisteredModel]:
        query = select(self.model).where(self.model.organization_id == organization_id)
        result = await db.execute(query)
        return result.scalars().all()

class ModelVersionRepository(BaseRepository[ModelVersion, Any, Any]):
    async def get_versions(self, db: AsyncSession, model_id: str) -> List[ModelVersion]:
        query = select(self.model).where(self.model.registered_model_id == model_id).order_by(self.model.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()

registered_model_repo = RegisteredModelRepository(RegisteredModel)
model_version_repo = ModelVersionRepository(ModelVersion)
