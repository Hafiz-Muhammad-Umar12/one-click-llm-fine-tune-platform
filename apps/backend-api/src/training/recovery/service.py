import uuid
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from opentelemetry import trace

from src.models.training import TrainingJob, TrainingFailureReport, TrainingEvent
from src.training.orchestrator.service import orchestrator_service
from src.training.kubernetes.job_manager import k8s_job_manager

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

class FailureRecoveryService:
    """
    Automated recovery engine for training workloads.
    """
    async def handle_job_failure(self, db: AsyncSession, job_id: uuid.UUID, error_code: str, error_message: str, stack_trace: str = None) -> bool:
        with tracer.start_as_current_span("handle_job_failure") as span:
            job = await db.get(TrainingJob, job_id)
            if not job:
                return False

            span.set_attribute("error_code", error_code)
            
            # 1. Determine if recoverable
            # E.g. NaN loss is fatal, Spot Preemption is recoverable
            is_recoverable = error_code not in ["NAN_LOSS", "INVALID_DATASET"]
            
            if is_recoverable and job.retry_count >= 3:
                is_recoverable = False
                error_message = f"Max retries (3) exceeded. Original error: {error_message}"

            # 2. Record Failure
            report = TrainingFailureReport(
                job_id=job.id,
                error_code=error_code,
                error_message=error_message,
                stack_trace=stack_trace,
                is_recoverable=is_recoverable
            )
            db.add(report)

            # 3. Clean up K8s
            if job.k8s_job_name:
                await k8s_job_manager.delete_job(job.k8s_job_name, job.k8s_namespace)

            # 4. State Transition
            if is_recoverable:
                job.state = "queued"
                job.retry_count += 1
                job.k8s_job_name = None
                
                event = TrainingEvent(
                    job_id=job.id,
                    event_type="JOB_RECOVERED",
                    message=f"Job marked for retry {job.retry_count}/3 after {error_code}",
                )
                db.add(event)
                logger.warning(f"Recovering Job {job_id} from {error_code}")
                
            else:
                job.state = "failed"
                event = TrainingEvent(
                    job_id=job.id,
                    event_type="JOB_FAILED",
                    message=f"Job failed permanently: {error_code}",
                )
                db.add(event)
                logger.error(f"Job {job_id} failed permanently: {error_code}")

            await db.commit()
            
            # If recoverable, in a real system we would trigger the orchestrator via a Celery beat 
            # or directly here to re-evaluate the queue.
            return is_recoverable

failure_recovery_service = FailureRecoveryService()
