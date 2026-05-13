from fastapi import Depends, Security
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.config import settings
from src.db.session import get_db
from src.repositories.user import user_repo
from src.security.jwt import decode_token
from src.exceptions.base import AuthenticationException
from src.models.models import User
from src.schemas.user import TokenPayload

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    try:
        payload = decode_token(token)
        token_data = TokenPayload(**payload)
        if token_data.type != "access":
            raise AuthenticationException(detail="Invalid token type")
    except (JWTError, Exception):
        raise AuthenticationException()
    
    user = await user_repo.get(db, id=token_data.sub)
    if not user:
        raise AuthenticationException(detail="User not found")
    if not user.is_active:
        raise AuthenticationException(detail="Inactive user")
    return user

async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_superuser:
        raise AuthenticationException(detail="The user doesn't have enough privileges")
    return current_user
