import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.deps.auth import get_current_user
from src.security.jwt import decode_token
from src.db.session import get_db
from src.models.models import User
from src.models.training import TrainingRun, TrainingJob
from src.schemas.training import TrainingRunCreate, TrainingRunResponse
from src.repositories.training import training_run_repo
from src.datasets.lineage.service import lineage_service
from src.training.orchestrator.service import orchestrator_service
from src.websocket.manager import manager

router = APIRouter()

@router.websocket("/{job_id}/ws")
async def training_websocket(
    websocket: WebSocket,
    job_id: str,
    token: str
):
    """
    Real-time streaming of training metrics and logs directly from Redis.
    """
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        await manager.connect(websocket, client_id=user_id)
        room_name = f"job:{job_id}:metrics" 
        await manager.subscribe_to_room(websocket, room_name)
    except Exception as e:
        await websocket.close()
    finally:
        manager.disconnect(user_id)


@router.post("/", response_model=TrainingRunResponse)
async def create_training_run(
    run_in: TrainingRunCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Creates a new training experiment tied to an immutable contract.
    """
    if not current_user.organizations:
        raise HTTPException(status_code=400, detail="User has no organization")
    
    org_id = current_user.organizations[0].id
    
    db_obj = TrainingRun(
        organization_id=org_id,
        contract_id=run_in.contract_id,
        name=run_in.name,
        training_config=run_in.training_config,
        status="pending"
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    
    return db_obj

@router.post("/{run_id}/launch")
async def launch_training(
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Hands off the training run to the distributed orchestration engine.
    """
    try:
        job = await orchestrator_service.launch_job(db, run_id)
        return {"job_id": str(job.id), "state": job.state}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{job_id}/cancel")
async def cancel_training(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Gracefully aborts a training job via K8s.
    """
    from src.training.kubernetes.job_manager import k8s_job_manager
    job = await db.get(TrainingJob, job_id)
    if not job:
        raise HTTPException(status_code=404)
        
    if job.k8s_job_name:
        await k8s_job_manager.delete_job(job.k8s_job_name, job.k8s_namespace)
        
    job.state = "cancelled"
    await db.commit()
    return {"status": "cancelled"}

@router.get("/{run_id}/lineage")
async def get_run_lineage(
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the complete lineage graph for a training run.
    """
    lineage = await lineage_service.get_run_lineage(db, run_id=run_id)
    if "error" in lineage:
        raise HTTPException(status_code=404, detail=lineage["error"])
    return lineage

@router.get("/", response_model=List[TrainingRunResponse])
async def list_training_runs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.organizations:
        return []
    org_id = current_user.organizations[0].id
    return await training_run_repo.get_by_org(db, organization_id=org_id)
