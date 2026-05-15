import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from opentelemetry import trace

from src.models.training import TrainingJob, TrainingRun, TrainingEvent
from src.training.runtimes.huggingface import TRLRuntime, AccelerateLauncher
from src.training.kubernetes.job_manager import k8s_job_manager
from src.training.schedulers.gpu_allocator import GPUAllocator
from src.training.services.checkpoints import checkpoint_service
from src.services.billing import usage_service

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

class OrchestratorService:
    """
    The brain of the training infrastructure.
    Coordinates between Database, Runtimes, Schedulers, and Kubernetes.
    """
    def __init__(self):
        self.allocator = GPUAllocator()
        self.runtime = TRLRuntime()
        self.launcher = AccelerateLauncher()

    async def launch_job(self, db: AsyncSession, run_id: uuid.UUID) -> TrainingJob:
        with tracer.start_as_current_span("orchestrator_launch_job") as span:
            span.set_attribute("run_id", str(run_id))
            
            run = await db.get(TrainingRun, run_id)
            if not run:
                raise ValueError("Training Run not found")

            # 1. Create Job Record
            job = TrainingJob(
                run_id=run_id,
                state="scheduling"
            )
            db.add(job)
            await db.flush() # Get ID
            
            # 2. Check Quotas & Hardware Allocation
            # In a real setup, we extract gpu_type and count from run.contract or run.training_config
            gpu_type = "NVIDIA_L4"
            gpu_count = 1
            can_allocate = await self.allocator.can_allocate(db, run.organization_id, gpu_count)
            if not can_allocate:
                job.state = "queued"
                await db.commit()
                return job

            # 3. Generate Runtime Command
            resume_uri = await checkpoint_service.get_resume_point(db, job.id)
            
            job_context = {
                "job_id": str(job.id),
                "model_name": run.contract.tokenizer_name if run.contract else "meta-llama/Llama-3-8b",
                "dataset_uri": "s3://mock-bucket/dataset.parquet", # from contract
                "hyperparameters": run.training_config,
                "checkpoint_dir": "/checkpoints"
            }
            
            base_cmd = self.runtime.generate_command(job_context)
            if resume_uri:
                base_cmd.extend(["--resume_from_checkpoint", resume_uri])
                
            hardware_context = {"num_gpus": gpu_count}
            final_cmd = self.launcher.wrap_command(base_cmd, hardware_context)
            
            # 4. Generate Kubernetes Manifest
            env_vars = self.runtime.prepare_environment(job_context)
            manifest = k8s_job_manager.manifest_builder.build_job_manifest(
                job_id=str(job.id),
                command=final_cmd,
                env_vars=env_vars,
                gpu_type=gpu_type,
                gpu_count=gpu_count
            )

            # 5. Submit to Execution Plane
            k8s_job_name = await k8s_job_manager.submit_job(manifest)
            
            job.k8s_job_name = k8s_job_name
            job.state = "running"
            run.status = "running"
            run.started_at = datetime.utcnow()
            
            # Audit Event
            event = TrainingEvent(
                job_id=job.id,
                event_type="JOB_LAUNCHED",
                message=f"Launched K8s Job {k8s_job_name} on {gpu_count}x {gpu_type}",
                metadata_payload={"cmd": final_cmd}
            )
            db.add(event)
            
            await db.commit()
            await db.refresh(job)
            return job

    async def complete_job(self, db: AsyncSession, job_id: uuid.UUID, final_state: str = "completed"):
        """
        Finalizes a training job and records usage for billing.
        """
        job = await db.get(TrainingJob, job_id)
        if not job:
            return

        run = await db.get(TrainingRun, job.run_id)
        job.state = final_state
        run.status = final_state
        run.completed_at = datetime.utcnow()

        # Calculate Usage (duration in seconds)
        if run.started_at:
            duration = (run.completed_at - run.started_at).total_seconds()
            await usage_service.record_usage(
                db, 
                organization_id=run.organization_id,
                resource_type="gpu_seconds",
                quantity=duration,
                unit="seconds",
                resource_id=str(job_id),
                metadata={"gpu_type": "NVIDIA_L4"}
            )

        db.add(job)
        db.add(run)
        await db.commit()

orchestrator_service = OrchestratorService()
