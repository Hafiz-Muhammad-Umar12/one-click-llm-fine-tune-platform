import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.deps.auth import get_current_user
from src.db.session import get_db
from src.models.models import User
from src.services.billing import billing_service, usage_service
from src.core.config import settings

router = APIRouter()

@router.post("/checkout")
async def create_checkout_session(
    price_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not user.organizations:
        raise HTTPException(status_code=400, detail="User has no organization")
    
    try:
        checkout_url = await billing_service.create_checkout_session(
            db, user.organizations[0].id, price_id
        )
        return {"checkout_url": checkout_url}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/usage")
async def get_org_usage(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not user.organizations:
        return []
    
    org_id = user.organizations[0].id
    gpu_usage = await usage_service.get_total_usage(db, org_id, "gpu_seconds")
    token_usage = await usage_service.get_total_usage(db, org_id, "inference_tokens")
    
    return {
        "gpu_seconds": gpu_usage,
        "inference_tokens": token_usage
    }

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    payload = await request.body()
    try:
        await billing_service.handle_webhook(db, payload.decode("utf-8"), stripe_signature)
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
