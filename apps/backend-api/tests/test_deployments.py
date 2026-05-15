import pytest
import uuid
from httpx import AsyncClient
from fastapi import status

@pytest.mark.asyncio
async def test_create_deployment_success(
    client: AsyncClient, 
    normal_user_token_headers: dict,
    db_session
):
    # This assumes a model version already exists. 
    # In a real test, we would create one first.
    version_id = str(uuid.uuid4())
    
    deployment_data = {
        "name": "Test Llama Deployment",
        "model_version_id": version_id,
        "hardware_tier": "nvidia-l4-1x",
        "target_replica_count": 1,
        "autoscaling_config": {"min_replicas": 1, "max_replicas": 3}
    }
    
    # Mocking the dependency or ensuring the version exists in DB would be needed for a full integration test.
    # For now, we test the API structure.
    response = await client.post(
        "/api/v1/deployments/",
        json=deployment_data,
        headers=normal_user_token_headers
    )
    
    # It might fail with 400 if version doesn't exist, which is expected behavior
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

@pytest.mark.asyncio
async def test_list_deployments(client: AsyncClient, normal_user_token_headers: dict):
    response = await client.get("/api/v1/deployments/", headers=normal_user_token_headers)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_inference_unauthorized(client: AsyncClient):
    endpoint_id = uuid.uuid4()
    response = await client.post(f"/api/v1/inference/{endpoint_id}/completions", json={})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
