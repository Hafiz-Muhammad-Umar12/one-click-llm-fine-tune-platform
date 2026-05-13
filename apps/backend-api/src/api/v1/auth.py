from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.deps.auth import get_current_user
from src.db.session import get_db
from src.schemas.user import Token, UserLogin, UserResponse, UserCreate
from src.services.auth import auth_service
from src.services.user import user_service
from src.models.models import User

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    login_in = UserLogin(email=form_data.username, password=form_data.password)
    return await auth_service.authenticate(db, login_in=login_in)

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh tokens
    """
    return await auth_service.refresh_token(db, refresh_token=refresh_token)

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current user
    """
    return current_user

@router.post("/register", response_model=UserResponse)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user
    """
    user = await user_service.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    return await user_service.create_user(db, user_in=user_in)
