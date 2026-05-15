import uuid
from typing import List, Optional, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.deployment import DeploymentEndpoint, DeploymentRevision, RollbackEvent
from src.repositories.base import BaseRepository

class DeploymentEndpointRepository(BaseRepository[DeploymentEndpoint, Any, Any]):
    async def get_by_org(
        self, db: AsyncSession, organization_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[DeploymentEndpoint]:
        query = (
            select(self.model)
            .where(self.model.organization_id == organization_id)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

class DeploymentRevisionRepository(BaseRepository[DeploymentRevision, Any, Any]):
    async def get_by_endpoint(self, db: AsyncSession, endpoint_id: uuid.UUID) -> List[DeploymentRevision]:
        query = (
            select(self.model)
            .where(self.model.endpoint_id == endpoint_id)
            .order_by(self.model.revision_number.desc())
        )
        result = await db.execute(query)
        return result.scalars().all()

class RollbackEventRepository(BaseRepository[RollbackEvent, Any, Any]):
    async def get_by_endpoint(self, db: AsyncSession, endpoint_id: uuid.UUID) -> List[RollbackEvent]:
        query = (
            select(self.model)
            .where(self.model.endpoint_id == endpoint_id)
            .order_by(self.model.created_at.desc())
        )
        result = await db.execute(query)
        return result.scalars().all()

deployment_endpoint_repo = DeploymentEndpointRepository(DeploymentEndpoint)
deployment_revision_repo = DeploymentRevisionRepository(DeploymentRevision)
rollback_event_repo = RollbackEventRepository(RollbackEvent)
