import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.training import TrainingCheckpoint, TrainingJob
from src.repositories.base import BaseRepository

class CheckpointRepository(BaseRepository[TrainingCheckpoint, Any, Any]):
    async def get_latest_for_job(self, db: AsyncSession, job_id: uuid.UUID) -> Optional[TrainingCheckpoint]:
        """
        Retrieves the most recent successful checkpoint for a given job.
        Used for failure recovery and resumability.
        """
        query = select(self.model).where(self.model.job_id == job_id).order_by(self.model.global_step.desc())
        result = await db.execute(query)
        return result.scalars().first()

checkpoint_repo = CheckpointRepository(TrainingCheckpoint)
