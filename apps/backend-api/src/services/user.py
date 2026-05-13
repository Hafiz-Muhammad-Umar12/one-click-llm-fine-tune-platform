from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.user import user_repo
from src.schemas.user import UserCreate
from src.security.password import get_password_hash

class UserService:
    async def create_user(self, db: AsyncSession, user_in: UserCreate):
        return await user_repo.create(db, obj_in=user_in)

    async def get_user_by_email(self, db: AsyncSession, email: str):
        return await user_repo.get_by_email(db, email=email)

user_service = UserService()
