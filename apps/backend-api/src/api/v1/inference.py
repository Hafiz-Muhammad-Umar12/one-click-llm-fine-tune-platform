import uuid
from typing import List, Dict, Any, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import json

from src.api.deps.auth import get_current_user
from src.db.session import get_db
from src.deployment.services.deployment import deployment_service
from src.deployment.security.inference_auth import get_inference_api_key
from src.models.models import User, APIKey

router = APIRouter()

@router.post("/{endpoint_id}/completions")
async def chat_completions(
    endpoint_id: uuid.UUID,
    request_data: Dict[str, Any],
    api_key: APIKey = Depends(get_inference_api_key),
    db: AsyncSession = Depends(get_db)
):
    """
    OpenAI-compatible chat completions proxy for a deployment endpoint.
    Routes the request to the underlying K8s service with tenant isolation.
    """
    endpoint = await deployment_service.get_deployment(db, endpoint_id)
    if not endpoint or endpoint.organization_id != api_key.organization_id:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    if endpoint.status != "active":
         raise HTTPException(status_code=400, detail=f"Endpoint is not active (status: {endpoint.status})")

    # The internal URL of the K8s service
    target_url = f"http://{endpoint.k8s_service_name}.default.svc.cluster.local:8000/v1/chat/completions"

    async def stream_proxy():
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", target_url, json=request_data) as response:
                if response.status_code != 200:
                    yield json.dumps({"error": "Upstream error", "status": response.status_code}).encode()
                    return

                async for chunk in response.aiter_bytes():
                    yield chunk

    if request_data.get("stream", False):
        return StreamingResponse(stream_proxy(), media_type="text/event-stream")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(target_url, json=request_data)
        return response.json()
