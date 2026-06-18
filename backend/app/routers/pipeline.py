from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.models.pipeline import PipelineStage, LeadPipeline
from app.models.lead import Lead
from app.schemas import (
    PipelineStageCreate, PipelineStageResponse, PipelineStageUpdate,
    LeadPipelineResponse,
)
from app.services.pipeline_service import PipelineService

router = APIRouter()


class MoveRequest(BaseModel):
    stage_id: UUID
    notes: Optional[str] = None


@router.get("/stages", response_model=list[PipelineStageResponse])
async def list_stages(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stages = await PipelineService.get_stages(db, current_user.id)
    results = []
    for stage in stages:
        lead_count_result = await db.execute(
            select(LeadPipeline).where(LeadPipeline.stage_id == stage.id)
        )
        leads = list(lead_count_result.scalars().all())
        results.append(
            PipelineStageResponse(
                id=stage.id,
                user_id=stage.user_id,
                name=stage.name,
                order=stage.position,
                color=stage.color,
                is_default=(stage.position == 0),
                lead_count=len(leads),
                created_at=stage.created_at,
                updated_at=stage.created_at,
            )
        )
    return results


@router.post("/stages", response_model=PipelineStageResponse, status_code=status.HTTP_201_CREATED)
async def create_stage(
    data: PipelineStageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stage = await PipelineService.create_stage(db, current_user.id, data.name, data.color or "#6366f1")
    return PipelineStageResponse(
        id=stage.id,
        user_id=stage.user_id,
        name=stage.name,
        order=stage.position,
        color=stage.color,
        is_default=False,
        lead_count=0,
        created_at=stage.created_at,
        updated_at=stage.created_at,
    )


@router.put("/stages/{stage_id}", response_model=PipelineStageResponse)
async def update_stage(
    stage_id: UUID,
    data: PipelineStageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        stage = await PipelineService.update_stage(db, stage_id, data.model_dump(exclude_unset=True))
        return PipelineStageResponse(
            id=stage.id,
            user_id=stage.user_id,
            name=stage.name,
            order=stage.position,
            color=stage.color,
            is_default=False,
            lead_count=0,
            created_at=stage.created_at,
            updated_at=stage.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/stages/{stage_id}")
async def delete_stage(
    stage_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await PipelineService.delete_stage(db, stage_id)
        return {"message": "Deleted"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/leads/{lead_id}/stage")
async def move_lead(
    lead_id: UUID,
    data: MoveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lead_result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.user_id == current_user.id)
    )
    lead = lead_result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    stage_result = await db.execute(
        select(PipelineStage).where(PipelineStage.id == data.stage_id)
    )
    stage = stage_result.scalar_one_or_none()
    if not stage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage not found")
    try:
        await PipelineService.move_lead(db, lead_id, data.stage_id)
        return {"message": "Lead moved"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/leads/{lead_id}", response_model=LeadPipelineResponse)
async def get_lead_pipeline(
    lead_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lead_result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.user_id == current_user.id)
    )
    lead = lead_result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    try:
        result = await db.execute(
            select(LeadPipeline).where(LeadPipeline.lead_id == lead_id)
        )
        lp = result.scalar_one_or_none()
        if not lp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not in pipeline")
        return lp
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
