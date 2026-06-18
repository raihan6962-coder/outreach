from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.models.sheet_source import SheetSource
from app.schemas import SheetSourceCreate, SheetSourceResponse, SheetSourceUpdate
from app.services.google_sheet_service import GoogleSheetService

router = APIRouter()


class SheetTestResponse(BaseModel):
    success: bool
    message: str
    lead_count: int = 0


@router.post("/", response_model=SheetSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_sheet_source(
    data: SheetSourceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    source = SheetSource(
        user_id=current_user.id,
        name=data.name,
        webhook_url=data.sheet_id,
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return SheetSourceResponse(
        id=source.id,
        user_id=source.user_id,
        name=source.name,
        sheet_id=source.webhook_url,
        sheet_name=None,
        sheet_range=None,
        column_mappings=None,
        header_row=1,
        data_start_row=2,
        import_interval_minutes=None,
        last_import_at=source.last_fetched_at,
        is_active=source.is_active,
        created_at=source.created_at,
        updated_at=source.created_at,
    )


@router.get("/", response_model=list[SheetSourceResponse])
async def list_sheet_sources(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SheetSource)
        .where(SheetSource.user_id == current_user.id)
        .order_by(SheetSource.created_at.desc())
    )
    sources = list(result.scalars().all())
    return [
        SheetSourceResponse(
            id=s.id,
            user_id=s.user_id,
            name=s.name,
            sheet_id=s.webhook_url,
            sheet_name=None,
            sheet_range=None,
            column_mappings=None,
            header_row=1,
            data_start_row=2,
            import_interval_minutes=None,
            last_import_at=s.last_fetched_at,
            is_active=s.is_active,
            created_at=s.created_at,
            updated_at=s.created_at,
        )
        for s in sources
    ]


@router.get("/{source_id}", response_model=SheetSourceResponse)
async def get_sheet_source(
    source_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SheetSource).where(SheetSource.id == source_id, SheetSource.user_id == current_user.id)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sheet source not found")
    return SheetSourceResponse(
        id=source.id,
        user_id=source.user_id,
        name=source.name,
        sheet_id=source.webhook_url,
        sheet_name=None,
        sheet_range=None,
        column_mappings=None,
        header_row=1,
        data_start_row=2,
        import_interval_minutes=None,
        last_import_at=source.last_fetched_at,
        is_active=source.is_active,
        created_at=source.created_at,
        updated_at=source.created_at,
    )


@router.put("/{source_id}", response_model=SheetSourceResponse)
async def update_sheet_source(
    source_id: UUID,
    data: SheetSourceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SheetSource).where(SheetSource.id == source_id, SheetSource.user_id == current_user.id)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sheet source not found")
    update_data = data.model_dump(exclude_unset=True)
    if "sheet_id" in update_data:
        source.webhook_url = update_data.pop("sheet_id")
    if "name" in update_data:
        source.name = update_data["name"]
    if "is_active" in update_data:
        source.is_active = update_data["is_active"]
    await db.commit()
    await db.refresh(source)
    return SheetSourceResponse(
        id=source.id,
        user_id=source.user_id,
        name=source.name,
        sheet_id=source.webhook_url,
        sheet_name=None,
        sheet_range=None,
        column_mappings=None,
        header_row=1,
        data_start_row=2,
        import_interval_minutes=None,
        last_import_at=source.last_fetched_at,
        is_active=source.is_active,
        created_at=source.created_at,
        updated_at=source.created_at,
    )


@router.delete("/{source_id}")
async def delete_sheet_source(
    source_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SheetSource).where(SheetSource.id == source_id, SheetSource.user_id == current_user.id)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sheet source not found")
    await db.delete(source)
    await db.commit()
    return {"message": "Deleted"}


@router.post("/{source_id}/test", response_model=SheetTestResponse)
async def test_sheet_source(
    source_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SheetSource).where(SheetSource.id == source_id, SheetSource.user_id == current_user.id)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sheet source not found")
    test_result = await GoogleSheetService.test_connection(source)
    return SheetTestResponse(
        success=test_result["success"],
        message=test_result["message"],
        lead_count=test_result.get("lead_count", 0),
    )


@router.post("/{source_id}/sync")
async def sync_sheet_source(
    source_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SheetSource).where(SheetSource.id == source_id, SheetSource.user_id == current_user.id)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sheet source not found")
    count = await GoogleSheetService.fetch_pending_leads(db, source, current_user.id)
    return {"message": "Sync started", "leads_fetched": count}
