import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.main import app
from src.db.base_class import Base
from src.db.session import get_db
import os

# Use an in-memory or temporary database for testing if possible
# Since we are using asyncpg, we'd normally need a real Postgres.
# For CI safety, we might want to mock the DB session or use a test DB env var.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/test_db")

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

from unittest.mock import MagicMock, AsyncMock

from src.security.password import get_password_hash
from src.api.deps.auth import get_current_user
from src.models.models import User

@pytest_asyncio.fixture
async def db_session():
    session = AsyncMock(spec=AsyncSession)
    
    # Mock result object
    mock_result = MagicMock()
    # Mock user object
    mock_user = MagicMock(spec=User)
    mock_user.hashed_password = get_password_hash("password123")
    mock_user.is_active = True
    mock_user.is_superuser = False
    mock_user.id = "mock_user_id"
    mock_user.organizations = []
    
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalars.return_value.first.return_value = None
    
    session.execute.return_value = mock_result
    yield session

@pytest.fixture(autouse=True)
def override_deps(db_session):
    async def _get_db():
        yield db_session
    
    async def _get_current_user():
        # Mock user object
        mock_user = MagicMock(spec=User)
        mock_user.hashed_password = get_password_hash("password123")
        mock_user.is_active = True
        mock_user.is_superuser = False
        mock_user.id = "mock_user_id"
        mock_user.organizations = []
        return mock_user

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_current_user] = _get_current_user
    yield
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)

@pytest.fixture
def normal_user_token_headers():
    return {"Authorization": "Bearer mock_token"}
