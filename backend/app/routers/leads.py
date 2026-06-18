from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import csv
import io
from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.models.lead import Lead
from app.schemas import LeadResponse, LeadUpdate, LeadBulkCreate

router = APIRouter()


class LeadFilter(BaseModel):
    query: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    score_min: Optional[int] = None
    score_max: Optional[int] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"
    page: int = 1
    page_size: int = 50


class LeadPageResponse(BaseModel):
    items: List[LeadResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class LeadBulkAction(BaseModel):
    lead_ids: List[UUID]
    action: str
    value: Optional[str] = None


class LeadTagUpdate(BaseModel):
    tags: List[str]


class LeadNoteCreate(BaseModel):
    note: str


@router.get("/", response_model=LeadPageResponse)
async def list_leads(
    filter: LeadFilter = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Lead).where(Lead.user_id == current_user.id)
    if filter.query:
        query = query.where(
            or_(
                Lead.email.ilike(f"%{filter.query}%"),
                Lead.app_name.ilike(f"%{filter.query}%"),
                Lead.developer.ilike(f"%{filter.query}%"),
            )
        )
    if filter.status:
        query = query.where(Lead.validation_status == filter.status)
    if filter.source:
        query = query.where(Lead.category == filter.source)
    if filter.company:
        query = query.where(Lead.developer.ilike(f"%{filter.company}%"))
    if filter.score_min is not None:
        query = query.where(Lead.score >= filter.score_min)
    if filter.score_max is not None:
        query = query.where(Lead.score <= filter.score_max)
    if filter.created_after:
        query = query.where(Lead.created_at >= filter.created_after)
    if filter.created_before:
        query = query.where(Lead.created_at <= filter.created_before)
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    sort_column = getattr(Lead, filter.sort_by, Lead.created_at)
    if filter.sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())
    offset = (filter.page - 1) * filter.page_size
    query = query.offset(offset).limit(filter.page_size)
    result = await db.execute(query)
    leads = list(result.scalars().all())
    total_pages = max(1, (total + filter.page_size - 1) // filter.page_size)
    return LeadPageResponse(
        items=[LeadResponse.model_validate(l) for l in leads],
        total=total,
        page=filter.page,
        page_size=filter.page_size,
        total_pages=total_pages,
        has_next=filter.page < total_pages,
        has_prev=filter.page > 1,
    )


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.user_id == current_user.id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    return lead


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: UUID,
    data: LeadUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.user_id == current_user.id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(lead, field):
            setattr(lead, field, value)
    await db.commit()
    await db.refresh(lead)
    return lead


@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.user_id == current_user.id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    await db.delete(lead)
    await db.commit()
    return {"message": "Deleted"}


@router.post("/bulk")
async def bulk_action(
    data: LeadBulkAction,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lead).where(
            Lead.id.in_(data.lead_ids),
            Lead.user_id == current_user.id,
        )
    )
    leads = list(result.scalars().all())
    if data.action == "delete":
        for lead in leads:
            await db.delete(lead)
    elif data.action == "tag":
        for lead in leads:
            tags = list(lead.tags or [])
            if data.value and data.value not in tags:
                tags.append(data.value)
            lead.tags = tags
    elif data.action == "status":
        for lead in leads:
            lead.validation_status = data.value or lead.validation_status
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown action: {data.action}")
    await db.commit()
    return {"message": "Action completed"}


@router.put("/{lead_id}/tags", response_model=LeadResponse)
async def update_lead_tags(
    lead_id: UUID,
    data: LeadTagUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.user_id == current_user.id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    lead.tags = data.tags
    await db.commit()
    await db.refresh(lead)
    return lead


@router.post("/{lead_id}/notes", response_model=LeadResponse)
async def add_lead_note(
    lead_id: UUID,
    data: LeadNoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.user_id == current_user.id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    notes = lead.notes or ""
    timestamp = datetime.utcnow().isoformat()
    lead.notes = f"{notes}\n[{timestamp}] {data.note}".strip()
    await db.commit()
    await db.refresh(lead)
    return lead


@router.post("/export")
async def export_leads(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lead).where(Lead.user_id == current_user.id).order_by(Lead.created_at.desc())
    )
    leads = list(result.scalars().all())
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "email", "app_name", "developer", "category", "installs", "score", "keyword", "validation_status", "is_sent", "created_at"])
    for lead in leads:
        writer.writerow([
            str(lead.id), lead.email, lead.app_name, lead.developer,
            lead.category, lead.installs, lead.score, lead.keyword,
            lead.validation_status, lead.is_sent, lead.created_at.isoformat() if lead.created_at else "",
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads_export.csv"},
    )


@router.post("/import")
async def import_leads(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    count = 0
    for row in reader:
        lead = Lead(
            user_id=current_user.id,
            email=row.get("email", ""),
            app_name=row.get("app_name", ""),
            developer=row.get("developer", ""),
            category=row.get("category", ""),
            keyword=row.get("keyword", ""),
            installs=int(row["installs"]) if row.get("installs") else None,
            score=float(row["score"]) if row.get("score") else None,
            validation_status="pending",
        )
        db.add(lead)
        count += 1
    await db.commit()
    return {"leads_imported": count}
