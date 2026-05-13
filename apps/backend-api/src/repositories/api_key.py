import secrets
import hashlib
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.models import APIKey
from src.repositories.base import BaseRepository
from src.schemas.user import TokenPayload # Using sub for consistency

class APIKeyRepository(BaseRepository[APIKey, Any, Any]):
    async def get_by_hash(self, db: AsyncSession, key_hash: str) -> Optional[APIKey]:
        query = select(self.model).where(self.model.key_hash == key_hash)
        result = await db.execute(query)
        return result.scalar_one_or_none()

api_key_repo = APIKeyRepository(APIKey)
