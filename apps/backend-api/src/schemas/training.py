import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

class TrainingRunBase(BaseModel):
    name: str
    contract_id: uuid.UUID
    training_config: Dict[str, Any] = {}

class TrainingRunCreate(TrainingRunBase):
    pass

class TrainingRunUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None

class TrainingRunResponse(TrainingRunBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    status: str
    metrics: Dict[str, Any]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)
