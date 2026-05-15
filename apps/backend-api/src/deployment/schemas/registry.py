import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict

class RegisteredModelBase(BaseModel):
    name: str
    description: Optional[str] = None

class RegisteredModelCreate(RegisteredModelBase):
    pass

class RegisteredModelResponse(RegisteredModelBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ModelVersionBase(BaseModel):
    version_tag: str
    base_model: str
    model_format: str
    metadata_info: Dict[str, Any] = {}

class ModelVersionCreate(ModelVersionBase):
    registered_model_id: uuid.UUID
    training_run_id: Optional[uuid.UUID] = None

class ModelVersionResponse(ModelVersionBase):
    id: uuid.UUID
    registered_model_id: uuid.UUID
    training_run_id: Optional[uuid.UUID]
    is_ready: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ModelArtifactResponse(BaseModel):
    id: uuid.UUID
    model_version_id: uuid.UUID
    artifact_type: str
    s3_uri: str
    file_size_bytes: int
    sha256_hash: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
