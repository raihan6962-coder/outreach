from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any


class CampaignStepCreate(BaseModel):
    order: int
    delay_days: int = 0
    subject: str
    body_html: str
    body_text: Optional[str] = None
    template_id: Optional[UUID] = None
    conditions: Optional[Dict[str, Any]] = None


class CampaignStepResponse(BaseModel):
    id: UUID
    campaign_id: UUID
    order: int
    delay_days: int
    subject: str
    body_html: str
    body_text: Optional[str]
    template_id: Optional[UUID]
    conditions: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class CampaignStepUpdate(BaseModel):
    order: Optional[int] = None
    delay_days: Optional[int] = None
    subject: Optional[str] = None
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    template_id: Optional[UUID] = None
    conditions: Optional[Dict[str, Any]] = None


class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    gmail_account_id: UUID
    sheet_source_id: Optional[UUID] = None
    lead_list_id: Optional[UUID] = None
    target_daily_sends: int = 50
    max_daily_sends: int = 100
    min_delay_seconds: int = 60
    max_delay_seconds: int = 180
    track_opens: bool = True
    track_clicks: bool = True
    bcc_address: Optional[str] = None
    reply_to: Optional[str] = None
    schedule_start_time: Optional[str] = None
    schedule_end_time: Optional[str] = None
    schedule_days: Optional[List[int]] = None
    timezone: str = "UTC"
    steps: Optional[List[CampaignStepCreate]] = None


class CampaignResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    gmail_account_id: UUID
    sheet_source_id: Optional[UUID]
    lead_list_id: Optional[UUID]
    status: str
    target_daily_sends: int
    max_daily_sends: int
    total_sent: int
    total_opens: int
    total_clicks: int
    total_replies: int
    total_bounces: int
    total_unsubscribes: int
    is_active: bool
    is_paused: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class CampaignDetailResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    gmail_account_id: UUID
    sheet_source_id: Optional[UUID]
    lead_list_id: Optional[UUID]
    status: str
    target_daily_sends: int
    max_daily_sends: int
    min_delay_seconds: int
    max_delay_seconds: int
    track_opens: bool
    track_clicks: bool
    bcc_address: Optional[str]
    reply_to: Optional[str]
    schedule_start_time: Optional[str]
    schedule_end_time: Optional[str]
    schedule_days: Optional[List[int]]
    timezone: str
    total_sent: int
    total_opens: int
    total_clicks: int
    total_replies: int
    total_bounces: int
    total_unsubscribes: int
    is_active: bool
    is_paused: bool
    steps: List[CampaignStepResponse]
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target_daily_sends: Optional[int] = None
    max_daily_sends: Optional[int] = None
    min_delay_seconds: Optional[int] = None
    max_delay_seconds: Optional[int] = None
    track_opens: Optional[bool] = None
    track_clicks: Optional[bool] = None
    bcc_address: Optional[str] = None
    reply_to: Optional[str] = None
    schedule_start_time: Optional[str] = None
    schedule_end_time: Optional[str] = None
    schedule_days: Optional[List[int]] = None
    timezone: Optional[str] = None


class CampaignScheduleRequest(BaseModel):
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    daily_limit: Optional[int] = None
    days_of_week: Optional[List[int]] = None
    timezone: str = "UTC"


class CampaignActionRequest(BaseModel):
    action: str
    reason: Optional[str] = None
