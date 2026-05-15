import uuid
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from opentelemetry import trace

from src.models.training import TrainingCheckpoint, TrainingEvent
from src.training.repositories.checkpoints import checkpoint_repo

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

class CheckpointService:
    async def register_checkpoint(
        self, 
        db: AsyncSession, 
        job_id: uuid.UUID, 
        s3_uri: str, 
        epoch: float, 
        global_step: int,
        metrics: Dict[str, Any]
    ) -> TrainingCheckpoint:
        
        with tracer.start_as_current_span("register_checkpoint") as span:
            span.set_attribute("job_id", str(job_id))
            span.set_attribute("epoch", epoch)
            span.set_attribute("global_step", global_step)

            checkpoint = TrainingCheckpoint(
                job_id=job_id,
                s3_uri=s3_uri,
                epoch=epoch,
                global_step=global_step,
                metrics_snapshot=metrics
            )
            
            # Record an event for audit and websockets
            event = TrainingEvent(
                job_id=job_id,
                event_type="CHECKPOINT_SAVED",
                message=f"Checkpoint saved at step {global_step} (Epoch {epoch:.2f})",
                metadata_payload={"s3_uri": s3_uri, "metrics": metrics}
            )

            db.add(checkpoint)
            db.add(event)
            await db.commit()
            await db.refresh(checkpoint)
            
            logger.info(f"Registered checkpoint for job {job_id} at step {global_step}")
            return checkpoint

    async def get_resume_point(self, db: AsyncSession, job_id: uuid.UUID) -> Optional[str]:
        """Returns the S3 URI of the latest checkpoint to resume from."""
        latest = await checkpoint_repo.get_latest_for_job(db, job_id)
        if latest:
            return latest.s3_uri
        return None

checkpoint_service = CheckpointService()
