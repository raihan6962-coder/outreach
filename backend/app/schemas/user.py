from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    company: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    company: Optional[str]
    is_active: bool
    settings: Optional[dict]
    created_at: datetime
    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    settings: Optional[dict] = None


class PasswordResetRequest(BaseModel):
    email: str


class PasswordReset(BaseModel):
    token: str
    new_password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


class UserSettings(BaseModel):
    theme: str = "light"
    email_notifications: bool = True
    campaign_notifications: bool = True
    reply_notifications: bool = True
