import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.deps.auth import get_current_user
from src.db.session import get_db
from src.models.models import User
from src.datasets.schemas.dataset import DatasetCreate, DatasetResponse, DatasetVersionResponse
from src.datasets.services.dataset import dataset_service
from src.datasets.repositories.dataset import dataset_repo, dataset_version_repo
from src.datasets.jobs.tasks import validate_dataset_task

router = APIRouter()

@router.post("/", response_model=DatasetResponse)
async def create_dataset(
    dataset_in: DatasetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # For now, use the user's first organization. 
    # In production, this would be passed via a header or project context.
    if not current_user.organizations:
        raise HTTPException(status_code=400, detail="User has no organization")
    
    org_id = current_user.organizations[0].id
    return await dataset_service.create_dataset(db, organization_id=org_id, dataset_in=dataset_in)

@router.get("/", response_model=List[DatasetResponse])
async def list_datasets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.organizations:
        return []
    org_id = current_user.organizations[0].id
    return await dataset_repo.get_by_org(db, organization_id=org_id)

@router.post("/{dataset_id}/upload", response_model=dict)
async def get_upload_url(
    dataset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify ownership
    dataset = await dataset_repo.get(db, id=dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    upload_url, file_path = await dataset_service.get_upload_params(dataset_id)
    return {"upload_url": upload_url, "file_path": file_path}

@router.post("/{dataset_id}/process", response_model=DatasetVersionResponse)
async def start_processing(
    dataset_id: uuid.UUID,
    file_path: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    version = await dataset_service.create_initial_version(
        db, dataset_id=dataset_id, s3_uri=file_path
    )
    
    # Trigger async validation task
    validate_dataset_task.delay(str(version.id))
    
    return version
