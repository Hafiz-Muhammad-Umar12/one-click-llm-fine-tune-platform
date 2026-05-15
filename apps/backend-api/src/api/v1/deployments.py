import uuid
from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps.auth import get_current_user
from src.db.session import get_db
from src.deployment.services.deployment import deployment_service
from src.deployment.schemas.deployment import DeploymentCreate, DeploymentResponse, DeploymentRevisionResponse
from src.models.models import User

router = APIRouter()

@router.post("/", response_model=DeploymentResponse)
async def create_deployment(
    deployment_in: DeploymentCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # For now, use the first organization the user belongs to
    if not user.organizations:
        raise HTTPException(status_code=400, detail="User has no organization")
    
    return await deployment_service.create_deployment(
        db, user.organizations[0].id, deployment_in
    )

@router.get("/", response_model=List[DeploymentResponse])
async def list_deployments(
    skip: int = 0,
    limit: int = 100,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not user.organizations:
        return []
    return await deployment_service.get_deployments(
        db, user.organizations[0].id, skip=skip, limit=limit
    )

@router.get("/{endpoint_id}", response_model=DeploymentResponse)
async def get_deployment(
    endpoint_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    deployment = await deployment_service.get_deployment(db, endpoint_id)
    if not deployment or (user.organizations and deployment.organization_id != user.organizations[0].id):
        raise HTTPException(status_code=404, detail="Deployment not found")
    return deployment

@router.post("/{endpoint_id}/rollback", response_model=DeploymentResponse)
async def rollback_deployment(
    endpoint_id: uuid.UUID,
    to_revision_id: uuid.UUID,
    reason: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        return await deployment_service.rollback_deployment(
            db, endpoint_id, to_revision_id, reason
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
