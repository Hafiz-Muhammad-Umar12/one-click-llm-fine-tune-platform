import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, DateTime, ForeignKey, Integer, Float, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base_class import Base

class UsageRecord(Base):
    """
    Time-series usage tracking for billing.
    Records GPU seconds, inference tokens, and dataset processing units.
    """
    __tablename__ = "usage_record"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organization.id", ondelete="CASCADE"), nullable=False, index=True)
    
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True) # gpu_seconds, inference_tokens, storage_gb
    resource_id: Mapped[Optional[str]] = mapped_column(String(255)) # ID of the job or deployment
    
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    unit: Mapped[str] = mapped_column(String(20), nullable=False) # seconds, tokens, gb-hours
    
    metadata_payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict) # e.g., {"gpu_type": "A100", "model": "llama-3"}
    
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    organization: Mapped["Organization"] = relationship()


class StripeCustomer(Base):
    """
    Maps an organization to its Stripe customer and subscription profile.
    """
    __tablename__ = "stripe_customer"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organization.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    stripe_customer_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    
    plan_tier: Mapped[str] = mapped_column(String(50), default="free")
    subscription_status: Mapped[str] = mapped_column(String(50), default="inactive") # active, past_due, canceled
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization: Mapped["Organization"] = relationship()
