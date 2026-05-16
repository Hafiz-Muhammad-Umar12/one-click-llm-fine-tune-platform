from typing import List, Optional, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.training import TrainingRun
from src.repositories.base import BaseRepository

class TrainingRunRepository(BaseRepository[TrainingRun, Any, Any]):
    async def get_by_org(self, db: AsyncSession, organization_id: str) -> List[TrainingRun]:
        query = select(self.model).where(self.model.organization_id == organization_id)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_contract(self, db: AsyncSession, contract_id: str) -> List[TrainingRun]:
        query = select(self.model).where(self.model.contract_id == contract_id)
        result = await db.execute(query)
        return result.scalars().all()

training_run_repo = TrainingRunRepository(TrainingRun)
