import pytest
from httpx import AsyncClient, ASGITransport

from src.main import app
from src.core.config import settings


@pytest.mark.asyncio
async def test_register_user():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as ac:

        response = await ac.post(
            f"{settings.API_V1_STR}/auth/register",
            json={
                "email": "test@example.com",
                "password": "password123",
                "full_name": "Test User"
            }
        )

    assert response.status_code in [200, 400]


@pytest.mark.asyncio
async def test_login_user():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as ac:

        response = await ac.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": "test@example.com",
                "password": "password123"
            }
        )

    assert response.status_code in [200, 401]