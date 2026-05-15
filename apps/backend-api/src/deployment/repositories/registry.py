import uuid
from typing import List, Optional, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.deployment import RegisteredModel, ModelVersion, ModelArtifact
from src.repositories.base import BaseRepository
from src.deployment.schemas.registry import RegisteredModelCreate, ModelVersionCreate

class RegisteredModelRepository(BaseRepository[RegisteredModel, RegisteredModelCreate, Any]):
    async def get_by_org(
        self, db: AsyncSession, organization_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[RegisteredModel]:
        query = (
            select(self.model)
            .where(self.model.organization_id == organization_id)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

class ModelVersionRepository(BaseRepository[ModelVersion, ModelVersionCreate, Any]):
    async def get_versions(
        self, db: AsyncSession, model_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[ModelVersion]:
        query = (
            select(self.model)
            .where(self.model.registered_model_id == model_id)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

class ModelArtifactRepository(BaseRepository[ModelArtifact, Any, Any]):
    async def get_by_version(self, db: AsyncSession, version_id: uuid.UUID) -> List[ModelArtifact]:
        query = select(self.model).where(self.model.model_version_id == version_id)
        result = await db.execute(query)
        return result.scalars().all()

registered_model_repo = RegisteredModelRepository(RegisteredModel)
model_version_repo = ModelVersionRepository(ModelVersion)
model_artifact_repo = ModelArtifactRepository(ModelArtifact)
