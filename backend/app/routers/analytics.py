from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.schemas.analytics import AnalyticsOverview, GmailHealthResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/overview")
async def get_overview(
    period: str = Query("all", regex="^(day|week|month|all)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    overview = await AnalyticsService.get_overview(db, current_user.id, period)
    return overview


@router.get("/daily")
async def get_daily_stats(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stats = await AnalyticsService.get_daily_stats(db, current_user.id, days)
    return stats


@router.get("/weekly")
async def get_weekly_stats(
    weeks: int = Query(12, ge=1, le=52),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stats = await AnalyticsService.get_weekly_stats(db, current_user.id, weeks)
    return stats


@router.get("/monthly")
async def get_monthly_stats(
    months: int = Query(12, ge=1, le=24),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stats = await AnalyticsService.get_monthly_stats(db, current_user.id, months)
    return stats


@router.get("/gmail-health")
async def get_gmail_health(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    health = await AnalyticsService.get_gmail_health(db, current_user.id)
    return health
