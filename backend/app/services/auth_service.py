from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_reset_token,
)
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.models.pipeline import PipelineStage


class AuthService:
    @staticmethod
    async def register_user(db: AsyncSession, user_data: UserCreate) -> User:
        existing = await db.execute(select(User).where(User.email == user_data.email))
        if existing.scalar_one_or_none():
            raise ValueError("Email already registered")
        user = User(
            email=user_data.email,
            password_hash=hash_password(user_data.password),
            full_name=user_data.full_name,
            company_name=user_data.company_name,
        )
        db.add(user)
        await db.flush()
        default_stages = [
            {"name": "New", "color": "#6B7280", "order": 0},
            {"name": "Contacted", "color": "#3B82F6", "order": 1},
            {"name": "Interested", "color": "#10B981", "order": 2},
            {"name": "Not Interested", "color": "#EF4444", "order": 3},
            {"name": "Replied", "color": "#8B5CF6", "order": 4},
            {"name": "Converted", "color": "#F59E0B", "order": 5},
        ]
        for stage_data in default_stages:
            stage = PipelineStage(
                user_id=user.id,
                name=stage_data["name"],
                color=stage_data["color"],
                order=stage_data["order"],
            )
            db.add(stage)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")
        return user

    @staticmethod
    def create_tokens(user: User) -> dict:
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    @staticmethod
    def refresh_access_token(refresh_token: str) -> str:
        payload = decode_token(refresh_token)
        if payload is None:
            raise ValueError("Invalid or expired refresh token")
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid refresh token payload")
        return create_access_token(
            data={"sub": user_id},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")
        return user

    @staticmethod
    async def update_user(db: AsyncSession, user_id: UUID, data: UserUpdate) -> User:
        user = await AuthService.get_user_by_id(db, user_id)
        update_data = data.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["password_hash"] = hash_password(update_data.pop("password"))
        for field, value in update_data.items():
            setattr(user, field, value)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def initiate_password_reset(db: AsyncSession, email: str) -> str:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")
        reset_token = generate_reset_token()
        user.reset_token = reset_token
        user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        await db.commit()
        return reset_token

    @staticmethod
    async def reset_password(db: AsyncSession, token: str, new_password: str) -> bool:
        result = await db.execute(
            select(User).where(
                User.reset_token == token,
                User.reset_token_expiry > datetime.utcnow(),
            )
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("Invalid or expired reset token")
        user.password_hash = hash_password(new_password)
        user.reset_token = None
        user.reset_token_expiry = None
        await db.commit()
        return True
