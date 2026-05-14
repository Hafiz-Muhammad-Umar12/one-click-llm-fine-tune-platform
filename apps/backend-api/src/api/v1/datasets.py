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

# New Imports for Phase 2.2
from src.datasets.preview.engine import DatasetPreviewEngine
from src.datasets.contracts.service import dataset_contract_service
from src.models.dataset import DatasetVersion

router = APIRouter()

@router.websocket("/{dataset_id}/ws")
async def dataset_websocket(
    websocket: WebSocket,
    dataset_id: str,
    token: str
):
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        await manager.connect(websocket, client_id=user_id)
        room_name = f"org:mock_org:dataset:{dataset_id}" 
        await manager.subscribe_to_room(websocket, room_name)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()
    finally:
        manager.disconnect(user_id)

@router.get("/{dataset_id}/versions/{version_id}/preview")
async def get_dataset_preview(
    dataset_id: uuid.UUID,
    version_id: uuid.UUID,
    tokenizer_name: str = "meta-llama/Llama-3-8b",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    version = await db.get(DatasetVersion, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    dataset = await db.get(Dataset, version.dataset_id)
    
    # In production, we'd stream a few lines from storage
    storage = dataset_service.storage
    file_stream = await storage.download_file(version.s3_uri)
    content = file_stream.read()
    
    from src.datasets.parsers.jsonl import JSONLParser
    parser = JSONLParser()
    data = parser.parse(content)
    
    preview_engine = DatasetPreviewEngine(tokenizer_name=tokenizer_name)
    return preview_engine.get_preview(data, format_type=dataset.base_format)

@router.post("/{dataset_id}/versions/{version_id}/finalize")
async def finalize_dataset(
    dataset_id: uuid.UUID,
    version_id: uuid.UUID,
    tokenizer_name: str,
    max_seq_length: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Finalizes a dataset version and generates the Training Contract.
    """
    return await dataset_contract_service.finalize_version(
        db, 
        dataset_version_id=version_id,
        tokenizer_name=tokenizer_name,
        max_seq_length=max_seq_length
    )

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
    process_dataset_task.delay(str(version.id))
    return version
