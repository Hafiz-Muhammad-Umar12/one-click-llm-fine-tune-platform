import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict

class DeploymentBase(BaseModel):
    name: str
    hardware_tier: str
    target_replica_count: int = 1
    autoscaling_config: Dict[str, Any] = {}

class DeploymentCreate(DeploymentBase):
    model_version_id: uuid.UUID

class DeploymentResponse(DeploymentBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    model_version_id: uuid.UUID
    status: str
    k8s_deployment_name: Optional[str]
    k8s_service_name: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class DeploymentRevisionResponse(BaseModel):
    id: uuid.UUID
    endpoint_id: uuid.UUID
    revision_number: int
    model_version_id: uuid.UUID
    config_snapshot: Dict[str, Any]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
