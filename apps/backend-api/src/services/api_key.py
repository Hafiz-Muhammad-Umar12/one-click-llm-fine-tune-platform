import secrets
import hashlib
from typing import Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.api_key import api_key_repo
from src.models.models import APIKey

class APIKeyService:
    def generate_key(self, prefix: str = "sk_live_") -> Tuple[str, str]:
        """
        Generates a new API key.
        Returns (raw_key, hashed_key)
        """
        raw_key = f"{prefix}{secrets.token_urlsafe(32)}"
        hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()
        return raw_key, hashed_key

    async def create_api_key(
        self, db: AsyncSession, *, organization_id: str, name: str, scopes: dict = None
    ) -> str:
        raw_key, hashed_key = self.generate_key()
        prefix = raw_key[:16]
        
        db_obj = APIKey(
            organization_id=organization_id,
            name=name,
            key_hash=hashed_key,
            prefix=prefix,
            scopes=scopes or {"permissions": []}
        )
        db.add(db_obj)
        await db.commit()
        return raw_key

    async def authenticate(self, db: AsyncSession, raw_key: str) -> Optional[APIKey]:
        hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = await api_key_repo.get_by_hash(db, hashed_key)
        if api_key:
            # Update last used at in background or after response
            return api_key
        return None

api_key_service = APIKeyService()
