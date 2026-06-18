from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, date
from typing import Optional, List


class WarmupConfigure(BaseModel):
    target_daily_sends: int = 20
    max_daily_sends: int = 50
    min_delay_seconds: int = 30
    max_delay_seconds: int = 120
    reply_probability: float = 0.1
    read_probability: float = 0.4
    reply_delay_minutes: int = 30
    is_active: bool = True
    schedule_start_time: Optional[str] = None
    schedule_end_time: Optional[str] = None
    schedule_days: Optional[List[int]] = None
    timezone: str = "UTC"


class WarmupStatusResponse(BaseModel):
    id: UUID
    gmail_account_id: UUID
    email: str
    is_active: bool
    is_paused: bool
    status: str
    current_daily_sends: int
    target_daily_sends: int
    max_daily_sends: int
    total_sent: int
    total_replies: int
    total_reads: int
    warmup_level: int
    sender_reputation: str
    sender_score: float
    started_at: Optional[datetime]
    last_activity_at: Optional[datetime]
    created_at: datetime
    model_config = {"from_attributes": True}


class WarmupProgressResponse(BaseModel):
    id: UUID
    gmail_account_id: UUID
    email: str
    warmup_level: int
    sender_score: float
    sender_reputation: str
    total_sent: int
    total_replies: int
    total_reads: int
    daily_progress: int
    daily_target: int
    days_active: int
    consistency_score: float
    weekly_stats: Optional[List["WarmupDailyStats"]]
    model_config = {"from_attributes": True}


class WarmupDailyStats(BaseModel):
    id: UUID
    warmup_id: UUID
    date: date
    sent: int
    replies: int
    reads: int
    bounces: int
    spam_reports: int
    reply_rate: float
    read_rate: float
    bounce_rate: float
    is_completed: bool
    created_at: datetime
    model_config = {"from_attributes": True}
