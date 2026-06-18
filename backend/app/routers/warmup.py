from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import date
from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.schemas import WarmupStatusResponse, WarmupConfigure, WarmupProgressResponse
from app.services.warmup_service import WarmupService

router = APIRouter()


class WarmupConfigureRequest(WarmupConfigure):
    gmail_account_id: UUID


@router.get("/status/{gmail_id}", response_model=WarmupStatusResponse)
async def get_warmup_status(
    gmail_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        status_data = await WarmupService.get_status(db, gmail_id)
        return WarmupStatusResponse(
            id=gmail_id,
            gmail_account_id=gmail_id,
            email=status_data["email"],
            is_active=status_data["is_warming_up"],
            is_paused=False,
            status="warming" if status_data["is_warming_up"] else "completed",
            current_daily_sends=status_data["current_level"],
            target_daily_sends=status_data["target_daily"],
            max_daily_sends=status_data["target_daily"],
            total_sent=sum(h["sent"] for h in status_data["history"]),
            total_replies=0,
            total_reads=0,
            warmup_level=status_data.get("days_completed", 0),
            sender_reputation="good",
            sender_score=status_data["progress_percent"],
            started_at=None,
            last_activity_at=None,
            created_at=None,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/configure", response_model=WarmupStatusResponse)
async def configure_warmup(
    data: WarmupConfigureRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        progress = await WarmupService.configure(db, data.gmail_account_id, data.target_daily_sends)
        return WarmupStatusResponse(
            id=progress.id,
            gmail_account_id=progress.gmail_account_id,
            email="",
            is_active=True,
            is_paused=False,
            status="warming",
            current_daily_sends=0,
            target_daily_sends=data.target_daily_sends,
            max_daily_sends=data.max_daily_sends,
            total_sent=0,
            total_replies=0,
            total_reads=0,
            warmup_level=0,
            sender_reputation="neutral",
            sender_score=0.0,
            started_at=None,
            last_activity_at=None,
            created_at=None,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/progress/{gmail_id}", response_model=list[WarmupProgressResponse])
async def get_warmup_progress(
    gmail_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        progress_records = await WarmupService.get_progress(db, gmail_id)
        return [
            WarmupProgressResponse(
                id=p.id,
                gmail_account_id=p.gmail_account_id,
                email="",
                warmup_level=p.target_count,
                sender_score=0.0,
                sender_reputation="neutral",
                total_sent=p.sent_count,
                total_replies=p.reply_count,
                total_reads=p.inbox_count,
                daily_progress=p.sent_count,
                daily_target=p.target_count,
                days_active=0,
                consistency_score=0.0,
            )
            for p in progress_records
        ]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
