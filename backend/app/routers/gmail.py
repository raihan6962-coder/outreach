from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.schemas import GmailAccountResponse, GmailAccountUpdate
from app.schemas.analytics import GmailHealthResponse
from app.services.gmail_service import GmailService

router = APIRouter()


class GmailAuthUrlResponse(BaseModel):
    auth_url: str


class GmailAccountToggle(BaseModel):
    is_active: bool


class GmailHealthResponseSimple(BaseModel):
    account_id: str
    email: str
    healthy: bool
    message: str
    daily_sent: Optional[int] = None
    daily_limit: Optional[int] = None
    hourly_sent: Optional[int] = None
    hourly_limit: Optional[int] = None


@router.get("/auth-url", response_model=GmailAuthUrlResponse)
async def get_auth_url(current_user: User = Depends(get_current_user)):
    auth_url = GmailService.get_auth_url()
    return GmailAuthUrlResponse(auth_url=auth_url)


@router.get("/callback", response_model=GmailAccountResponse)
async def handle_callback(
    code: str = Query(...),
    state: str = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        account = await GmailService.handle_callback(db, current_user.id, code)
        return account
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/accounts", response_model=list[GmailAccountResponse])
async def list_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    accounts = await GmailService.get_accounts(db, current_user.id)
    return accounts


@router.get("/accounts/{account_id}", response_model=GmailAccountResponse)
async def get_account(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        account = await GmailService.get_account(db, account_id)
        return account
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/accounts/{account_id}", response_model=GmailAccountResponse)
async def update_account(
    account_id: UUID,
    data: GmailAccountUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        account = await GmailService.update_account(db, account_id, data.model_dump(exclude_unset=True))
        return account
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/accounts/{account_id}")
async def disconnect_account(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await GmailService.disconnect_account(db, account_id)
        return {"message": "Disconnected"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/accounts/{account_id}/toggle", response_model=GmailAccountResponse)
async def toggle_account(
    account_id: UUID,
    data: GmailAccountToggle,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        account = await GmailService.toggle_account(db, account_id, data.is_active)
        return account
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/accounts/{account_id}/health", response_model=GmailHealthResponseSimple)
async def check_account_health(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        health = await GmailService.check_account_health(db, account_id)
        return health
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
