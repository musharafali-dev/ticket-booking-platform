"""Auth API routes: register, verify email, login, refresh, current user."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import service
from app.auth.models import User
from app.auth.schemas import (
    UserRegister,
    UserLogin,
    TokenResponse,
    RefreshRequest,
    UserResponse,
    MessageResponse,
)
from app.common.dependencies import get_current_user
from app.database import get_db

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    user = await service.register_user(db, data)
    return user


@router.get("/verify-email", response_model=MessageResponse)
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    await service.verify_email(db, token)
    return {"message": "Email verified successfully. You can now log in."}


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await service.authenticate_user(db, data.email, data.password)
    access_token, refresh_token = await service.issue_tokens(db, user)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    access_token, refresh_token = await service.rotate_refresh_token(
        db, data.refresh_token
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
