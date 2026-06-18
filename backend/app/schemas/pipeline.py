from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List


class PipelineStageCreate(BaseModel):
    name: str
    order: int
    color: Optional[str] = None
    is_default: bool = False


class PipelineStageResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    order: int
    color: Optional[str]
    is_default: bool
    lead_count: Optional[int]
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class PipelineStageUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    is_default: Optional[bool] = None


class LeadPipelineCreate(BaseModel):
    lead_id: UUID
    stage_id: UUID
    campaign_id: Optional[UUID] = None
    notes: Optional[str] = None


class LeadPipelineResponse(BaseModel):
    id: UUID
    lead_id: UUID
    stage_id: UUID
    campaign_id: Optional[UUID]
    entered_at: datetime
    exited_at: Optional[datetime]
    time_in_stage_seconds: Optional[int]
    is_current: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class LeadPipelineUpdate(BaseModel):
    stage_id: Optional[UUID] = None
    notes: Optional[str] = None


class PipelineStageOrderUpdate(BaseModel):
    stage_ids: List[UUID]


class PipelineStageMoveRequest(BaseModel):
    lead_pipeline_id: UUID
    target_stage_id: UUID
    notes: Optional[str] = None
