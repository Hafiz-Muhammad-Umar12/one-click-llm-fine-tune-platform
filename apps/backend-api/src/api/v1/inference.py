import uuid
from typing import List, Dict, Any, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from src.core.ratelimit import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import json

from src.api.deps.auth import get_current_user
from src.db.session import get_db
from src.deployment.services.deployment import deployment_service
from src.deployment.security.inference_auth import get_inference_api_key
from src.models.models import User, APIKey
from src.services.billing import usage_service

router = APIRouter()

@router.post(
    "/{endpoint_id}/completions",
    dependencies=[Depends(RateLimiter(times=100, minutes=1))]
)
async def chat_completions(
    endpoint_id: uuid.UUID,
    request_data: Dict[str, Any],
    api_key: APIKey = Depends(get_inference_api_key),
    db: AsyncSession = Depends(get_db)
):
    """
    OpenAI-compatible chat completions proxy for a deployment endpoint.
    Supports Structured Generation via guided decoding (JSON, Regex, Choice).
    """
    endpoint = await deployment_service.get_deployment(db, endpoint_id)
    if not endpoint or endpoint.organization_id != api_key.organization_id:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    if endpoint.status != "active":
         raise HTTPException(status_code=400, detail=f"Endpoint is not active (status: {endpoint.status})")

    # Map Structured Generation parameters for vLLM
    # Supported: guided_json, guided_regex, guided_choice
    guided_params = {}
    for key in ["guided_json", "guided_regex", "guided_choice", "guided_grammar"]:
        if key in request_data:
            guided_params[key] = request_data.pop(key)

    # The internal URL of the K8s service
    target_url = f"http://{endpoint.k8s_service_name}.default.svc.cluster.local:8000/v1/chat/completions"

    # Merge guided params back if using a custom vLLM version or specialized handler
    # For standard vLLM OpenAI API, these often go in the top level or extra_body
    final_payload = {**request_data, **guided_params}

    async def stream_proxy():
        total_tokens = 0
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", target_url, json=request_data) as response:
                if response.status_code != 200:
                    yield json.dumps({"error": "Upstream error", "status": response.status_code}).encode()
                    return

                async for chunk in response.aiter_bytes():
                    # Simple heuristic for token count in stream (1 token ~ 4 chars)
                    total_tokens += len(chunk) // 4 
                    yield chunk
        
        # Record Streamed Tokens
        await usage_service.record_usage(
            db,
            organization_id=api_key.organization_id,
            resource_type="inference_tokens",
            quantity=float(total_tokens),
            unit="tokens",
            resource_id=str(endpoint_id)
        )

    if request_data.get("stream", False):
        return StreamingResponse(stream_proxy(), media_type="text/event-stream")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(target_url, json=request_data)
        res_json = response.json()
        
        # Record Tokens from response usage field
        usage = res_json.get("usage", {})
        total_tokens = usage.get("total_tokens", 0)
        
        await usage_service.record_usage(
            db,
            organization_id=api_key.organization_id,
            resource_type="inference_tokens",
            quantity=float(total_tokens),
            unit="tokens",
            resource_id=str(endpoint_id)
        )
        
        return res_json
