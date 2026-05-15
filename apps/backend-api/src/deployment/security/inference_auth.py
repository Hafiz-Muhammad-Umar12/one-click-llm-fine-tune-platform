from fastapi import Security, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import get_db
from src.services.api_key import api_key_service
from src.models.models import APIKey

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

async def get_inference_api_key(
    header_key: str = Security(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> APIKey:
    if not header_key:
        raise HTTPException(status_code=401, detail="Missing API Key")
        
    # Standard format is 'Bearer <key>'
    token = header_key.split(" ")[-1] if " " in header_key else header_key
    
    key = await api_key_service.authenticate(db, token)
    if not key:
        raise HTTPException(status_code=401, detail="Invalid API Key")
        
    return key
