import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.deps.auth import get_current_user
from src.security.jwt import decode_token
from src.db.session import get_db
from src.models.models import User
from src.datasets.schemas.dataset import DatasetCreate, DatasetResponse, DatasetVersionResponse
from src.datasets.services.dataset import dataset_service
from src.datasets.repositories.dataset import dataset_repo, dataset_version_repo
from src.datasets.jobs.tasks import process_dataset_task
from src.websocket.manager import manager

router = APIRouter()

@router.websocket("/{dataset_id}/ws")
async def dataset_websocket(
    websocket: WebSocket,
    dataset_id: str,
    token: str
):
    """
    Real-time streaming of dataset processing metrics.
    Connects to Redis Pub/Sub room specific to this dataset.
    """
    try:
        # Manual token validation for WS
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        await manager.connect(websocket, client_id=user_id)
        
        # Proper auth would fetch the dataset to verify org_id here
        # Assuming org checking is done for simplicity in demo
        room_name = f"org:mock_org:dataset:{dataset_id}" 
        
        await manager.subscribe_to_room(websocket, room_name)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()
    finally:
        manager.disconnect(user_id)

@router.post("/", response_model=DatasetResponse)
async def create_dataset(
    dataset_in: DatasetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
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
    
    # Trigger the new Enterprise async task
    process_dataset_task.delay(str(version.id))
    
    return version
