import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base_class import Base

class TrainingRun(Base):
    """
    Lineage tracking for training experiments.
    Connects a training execution to its immutable DatasetTrainingContract.
    """
    __tablename__ = "training_run"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organization.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Lineage & Reproducibility
    contract_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("dataset_training_contract.id"), nullable=False)
    
    # Run Metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    
    # Config Snapshot
    training_config: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Results
    metrics: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    contract: Mapped["DatasetTrainingContract"] = relationship()
    organization: Mapped["Organization"] = relationship()
