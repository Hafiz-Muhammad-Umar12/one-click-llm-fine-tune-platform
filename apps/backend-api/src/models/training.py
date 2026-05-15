import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base_class import Base

class TrainingRun(Base):
    """
    Lineage tracking for training experiments.
    Connects a training execution to its immutable DatasetTrainingContract.
    This represents the 'Intent' and hyperparameter configuration.
    """
    __tablename__ = "training_run"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organization.id", ondelete="CASCADE"), nullable=False, index=True)
    contract_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("dataset_training_contract.id"), nullable=False)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    training_config: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    metrics: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    contract: Mapped["DatasetTrainingContract"] = relationship()
    organization: Mapped["Organization"] = relationship()
    jobs: Mapped[List["TrainingJob"]] = relationship(back_populates="run", cascade="all, delete-orphan")
    artifacts: Mapped[List["TrainingArtifact"]] = relationship(back_populates="run", cascade="all, delete-orphan")


class TrainingJob(Base):
    """
    The actual execution instance of a TrainingRun on the Kubernetes cluster.
    Handles retries, pauses, and Kubernetes orchestration state.
    """
    __tablename__ = "training_job"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("training_run.id", ondelete="CASCADE"), nullable=False, index=True)
    
    k8s_job_name: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    k8s_namespace: Mapped[str] = mapped_column(String(50), default="tenant-workloads")
    state: Mapped[str] = mapped_column(String(50), default="queued") # queued, scheduling, running, completed, failed, paused
    
    priority: Mapped[int] = mapped_column(Integer, default=0)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    run: Mapped["TrainingRun"] = relationship(back_populates="jobs")
    events: Mapped[List["TrainingEvent"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    checkpoints: Mapped[List["TrainingCheckpoint"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    failure_reports: Mapped[List["TrainingFailureReport"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    allocations: Mapped[List["GPUAllocation"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class TrainingCheckpoint(Base):
    """
    Tracks saved weights during training for resumability and artifact management.
    """
    __tablename__ = "training_checkpoint"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("training_job.id", ondelete="CASCADE"), nullable=False, index=True)
    
    epoch: Mapped[float] = mapped_column(Float, nullable=False)
    global_step: Mapped[int] = mapped_column(Integer, nullable=False)
    s3_uri: Mapped[str] = mapped_column(String(512), nullable=False)
    
    metrics_snapshot: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    is_best: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job: Mapped["TrainingJob"] = relationship(back_populates="checkpoints")


class TrainingEvent(Base):
    """
    Immutable event log for the training lifecycle (e.g., "Pod Scheduled", "OOM Detected").
    Used for audit trails and WebSocket replay.
    """
    __tablename__ = "training_event"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("training_job.id", ondelete="CASCADE"), nullable=False, index=True)
    
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job: Mapped["TrainingJob"] = relationship(back_populates="events")


class TrainingFailureReport(Base):
    """
    Detailed root-cause analysis for failed jobs to assist in automated recovery.
    """
    __tablename__ = "training_failure_report"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("training_job.id", ondelete="CASCADE"), nullable=False, index=True)
    
    error_code: Mapped[str] = mapped_column(String(50), nullable=False) # e.g., CUDA_OOM, NODE_PREEMPTED
    error_message: Mapped[Text] = mapped_column(Text, nullable=False)
    stack_trace: Mapped[Optional[str]] = mapped_column(Text)
    is_recoverable: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job: Mapped["TrainingJob"] = relationship(back_populates="failure_reports")


class TrainingNode(Base):
    """
    Tracks available GPU worker nodes in the Kubernetes cluster.
    """
    __tablename__ = "training_node"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hostname: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    instance_type: Mapped[str] = mapped_column(String(50), nullable=False)
    gpu_type: Mapped[str] = mapped_column(String(50), nullable=False)
    gpu_count: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    last_heartbeat: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    allocations: Mapped[List["GPUAllocation"]] = relationship(back_populates="node")


class GPUAllocation(Base):
    """
    Maps a running job to specific GPUs on a TrainingNode.
    """
    __tablename__ = "gpu_allocation"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("training_job.id", ondelete="CASCADE"), nullable=False)
    node_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("training_node.id", ondelete="CASCADE"), nullable=False)
    
    gpu_indices: Mapped[List[int]] = mapped_column(JSONB, nullable=False) # e.g., [0, 1] for 2 GPUs
    allocated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    released_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    job: Mapped["TrainingJob"] = relationship(back_populates="allocations")
    node: Mapped["TrainingNode"] = relationship(back_populates="allocations")


class TrainingArtifact(Base):
    """
    Final output artifacts (e.g., LoRA adapter weights, fused model, logs archive).
    """
    __tablename__ = "training_artifact"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("training_run.id", ondelete="CASCADE"), nullable=False)
    
    artifact_type: Mapped[str] = mapped_column(String(50), nullable=False) # lora_adapter, full_weights, logs
    s3_uri: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    run: Mapped["TrainingRun"] = relationship(back_populates="artifacts")
