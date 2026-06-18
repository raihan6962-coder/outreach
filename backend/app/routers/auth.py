from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.schemas import (
    UserCreate, UserLogin, UserResponse, TokenResponse, TokenRefresh,
    PasswordResetRequest, PasswordReset, UserSettings, UserUpdate,
)
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        user = await AuthService.register_user(db, user_data)
        return AuthService.create_tokens(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    try:
        user = await AuthService.authenticate_user(db, credentials.email, credentials.password)
        return AuthService.create_tokens(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: TokenRefresh):
    try:
        access_token = AuthService.refresh_access_token(data.refresh_token)
        return TokenResponse(access_token=access_token, refresh_token=data.refresh_token, token_type="bearer")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/forgot-password")
async def forgot_password(data: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    try:
        await AuthService.initiate_password_reset(db, data.email)
        return {"message": "Reset email sent"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/reset-password")
async def reset_password(data: PasswordReset, db: AsyncSession = Depends(get_db)):
    try:
        await AuthService.reset_password(db, data.token, data.new_password)
        return {"message": "Password reset successful"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/settings", response_model=UserResponse)
async def update_settings(
    settings: UserSettings,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    update_data = UserUpdate(settings=settings.model_dump())
    try:
        user = await AuthService.update_user(db, current_user.id, update_data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
