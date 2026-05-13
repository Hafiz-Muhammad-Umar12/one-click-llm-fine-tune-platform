import uuid
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from src.models.dataset import DatasetStatus

class DatasetBase(BaseModel):
    name: str
    description: Optional[str] = None
    base_format: str

class DatasetCreate(DatasetBase):
    pass

class DatasetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[DatasetStatus] = None

class DatasetResponse(DatasetBase):
    id: uuid.UUID
    status: DatasetStatus
    organization_id: uuid.UUID
    
    model_config = ConfigDict(from_attributes=True)

class DatasetVersionResponse(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    version_number: int
    s3_uri: str
    status: DatasetStatus
    metadata_info: dict
    statistics: Optional[dict]
    
    model_config = ConfigDict(from_attributes=True)
