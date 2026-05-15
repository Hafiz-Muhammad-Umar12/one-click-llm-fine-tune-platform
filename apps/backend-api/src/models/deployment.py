import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base_class import Base

class RegisteredModel(Base):
    """
    Top-level logical model grouping for versioning (e.g., 'Customer Support Bot').
    """
    __tablename__ = "registered_model"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organization.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization: Mapped["Organization"] = relationship()
    versions: Mapped[List["ModelVersion"]] = relationship(back_populates="registered_model", cascade="all, delete-orphan")


class ModelVersion(Base):
    """
    Immutable snapshot tied to a specific training run.
    """
    __tablename__ = "model_version"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    registered_model_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("registered_model.id", ondelete="CASCADE"), nullable=False, index=True)
    training_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("training_run.id", ondelete="SET NULL"))
    
    version_tag: Mapped[str] = mapped_column(String(50), nullable=False) # e.g., "v1.0.0"
    base_model: Mapped[str] = mapped_column(String(255), nullable=False) # e.g., "meta-llama/Llama-3-8b"
    model_format: Mapped[str] = mapped_column(String(50), nullable=False) # "lora", "full", "gguf"
    
    metadata_info: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    is_ready: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    registered_model: Mapped["RegisteredModel"] = relationship(back_populates="versions")
    training_run: Mapped[Optional["TrainingRun"]] = relationship()
    artifacts: Mapped[List["ModelArtifact"]] = relationship(back_populates="model_version", cascade="all, delete-orphan")
    deployments: Mapped[List["DeploymentEndpoint"]] = relationship(back_populates="model_version")


class ModelArtifact(Base):
    """
    Specific binary artifacts (weights, configs) associated with a ModelVersion.
    """
    __tablename__ = "model_artifact"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("model_version.id", ondelete="CASCADE"), nullable=False, index=True)
    
    artifact_type: Mapped[str] = mapped_column(String(50), nullable=False) # "adapter_config", "adapter_model", "tokenizer"
    s3_uri: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    sha256_hash: Mapped[Optional[str]] = mapped_column(String(64))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    model_version: Mapped["ModelVersion"] = relationship(back_populates="artifacts")


class DeploymentEndpoint(Base):
    """
    Active inference endpoint routing traffic to K8s pods.
    """
    __tablename__ = "deployment_endpoint"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organization.id", ondelete="CASCADE"), nullable=False, index=True)
    model_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("model_version.id", ondelete="RESTRICT"), nullable=False)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="deploying") # deploying, active, scaled_to_zero, failed, terminated
    target_replica_count: Mapped[int] = mapped_column(Integer, default=1)
    k8s_deployment_name: Mapped[Optional[str]] = mapped_column(String(255))
    k8s_service_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    hardware_tier: Mapped[str] = mapped_column(String(50), nullable=False) # e.g., "nvidia-l4-1x"
    autoscaling_config: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization: Mapped["Organization"] = relationship()
    model_version: Mapped["ModelVersion"] = relationship(back_populates="deployments")
    revisions: Mapped[List["DeploymentRevision"]] = relationship(back_populates="endpoint", cascade="all, delete-orphan")


class DeploymentRevision(Base):
    """
    Immutable snapshot of a deployment configuration for rollback capability.
    """
    __tablename__ = "deployment_revision"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    endpoint_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("deployment_endpoint.id", ondelete="CASCADE"), nullable=False, index=True)
    
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    model_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("model_version.id"), nullable=False)
    config_snapshot: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    endpoint: Mapped["DeploymentEndpoint"] = relationship(back_populates="revisions")


class RollbackEvent(Base):
    """
    Tracks rollback actions for audit and debugging.
    """
    __tablename__ = "rollback_event"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    endpoint_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("deployment_endpoint.id", ondelete="CASCADE"), nullable=False)
    from_revision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("deployment_revision.id"), nullable=False)
    to_revision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("deployment_revision.id"), nullable=False)
    
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class InferenceMetrics(Base):
    """
    Aggregated inference metrics for autoscaling and billing.
    """
    __tablename__ = "inference_metrics"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    endpoint_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("deployment_endpoint.id", ondelete="CASCADE"), nullable=False, index=True)
    
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    total_requests: Mapped[int] = mapped_column(Integer, default=0)
    avg_latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    p99_latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    avg_ttft_ms: Mapped[float] = mapped_column(Float, default=0.0) # Time to first token
    avg_tpot_ms: Mapped[float] = mapped_column(Float, default=0.0) # Time per output token
    error_count: Mapped[int] = mapped_column(Integer, default=0)


class InferenceEvent(Base):
    """
    Granular tracing for specific inference failures or notable events.
    """
    __tablename__ = "inference_event"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    endpoint_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("deployment_endpoint.id", ondelete="CASCADE"), nullable=False)
    
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[Text] = mapped_column(Text, nullable=False)
    trace_id: Mapped[Optional[str]] = mapped_column(String(100)) # OpenTelemetry Trace ID
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
