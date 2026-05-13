from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.user import user_repo
from src.schemas.user import Token, UserLogin
from src.security.password import verify_password
from src.security.jwt import create_access_token, create_refresh_token
from src.exceptions.base import AuthenticationException

class AuthService:
    async def authenticate(self, db: AsyncSession, login_in: UserLogin) -> Token:
        user = await user_repo.get_by_email(db, email=login_in.email)
        if not user or not verify_password(login_in.password, user.hashed_password):
            raise AuthenticationException(detail="Incorrect email or password")
        
        if not user.is_active:
            raise AuthenticationException(detail="Inactive user")

        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token
        )

    async def refresh_token(self, db: AsyncSession, refresh_token: str) -> Token:
        # Simplified for now, rotation logic would involve checking token in Redis/DB
        from src.security.jwt import decode_token
        from jose import JWTError
        
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise AuthenticationException(detail="Invalid token type")
            user_id = payload.get("sub")
            if not user_id:
                raise AuthenticationException()
        except JWTError:
            raise AuthenticationException()

        access_token = create_access_token(subject=user_id)
        new_refresh_token = create_refresh_token(subject=user_id)
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token
        )

auth_service = AuthService()
