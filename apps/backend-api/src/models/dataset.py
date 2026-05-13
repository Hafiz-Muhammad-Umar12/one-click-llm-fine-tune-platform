import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base_class import Base

class DatasetStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"

class Dataset(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organization.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    base_format: Mapped[str] = mapped_column(String(50), nullable=False) # alpaca, chatml, etc.
    status: Mapped[DatasetStatus] = mapped_column(String(20), default=DatasetStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    versions: Mapped[List["DatasetVersion"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")
    organization: Mapped["Organization"] = relationship()

class DatasetVersion(Base):
    __tablename__ = "dataset_version"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("dataset.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    s3_uri: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[DatasetStatus] = mapped_column(String(20), default=DatasetStatus.PENDING)
    metadata_info: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    statistics: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    dataset: Mapped["Dataset"] = relationship(back_populates="versions")
    processing_jobs: Mapped[List["DatasetProcessingJob"]] = relationship(back_populates="dataset_version")

class DatasetProcessingJob(Base):
    __tablename__ = "dataset_processing_job"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("dataset_version.id", ondelete="CASCADE"), nullable=False)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False) # validation, preprocessing, etc.
    status: Mapped[str] = mapped_column(String(20), default="queued")
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    dataset_version: Mapped["DatasetVersion"] = relationship(back_populates="processing_jobs")
