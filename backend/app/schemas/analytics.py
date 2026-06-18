from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, date
from typing import Optional, List


class AnalyticsOverview(BaseModel):
    total_campaigns: int
    active_campaigns: int
    total_leads: int
    total_sent: int
    total_opens: int
    total_clicks: int
    total_replies: int
    total_bounces: int
    total_unsubscribes: int
    open_rate: float
    click_rate: float
    reply_rate: float
    bounce_rate: float
    unsubscribe_rate: float
    total_gmail_accounts: int
    active_gmail_accounts: int
    gmail_health_score: float


class AnalyticsDaily(BaseModel):
    id: UUID
    user_id: UUID
    date: date
    sent: int
    opens: int
    unique_opens: int
    clicks: int
    unique_clicks: int
    replies: int
    positive_replies: int
    bounces: int
    unsubscribes: int
    spam_reports: int
    created_at: datetime
    model_config = {"from_attributes": True}


class AnalyticsWeekly(BaseModel):
    id: UUID
    user_id: UUID
    week_start: date
    week_end: date
    sent: int
    opens: int
    unique_opens: int
    clicks: int
    unique_clicks: int
    replies: int
    positive_replies: int
    bounces: int
    unsubscribes: int
    spam_reports: int
    created_at: datetime
    model_config = {"from_attributes": True}


class AnalyticsMonthly(BaseModel):
    id: UUID
    user_id: UUID
    month: date
    sent: int
    opens: int
    unique_opens: int
    clicks: int
    unique_clicks: int
    replies: int
    positive_replies: int
    bounces: int
    unsubscribes: int
    spam_reports: int
    created_at: datetime
    model_config = {"from_attributes": True}


class AnalyticsDateRange(BaseModel):
    start_date: date
    end_date: date


class GmailHealthResponse(BaseModel):
    gmail_account_id: UUID
    email: str
    is_authenticated: bool
    is_active: bool
    daily_sent: int
    daily_limit: int
    daily_remaining: int
    bounce_rate: float
    spam_rate: float
    reply_rate: float
    health_score: float
    status: str
    last_checked_at: Optional[datetime]
    issues: Optional[List[str]]


class CampaignAnalyticsResponse(BaseModel):
    campaign_id: UUID
    campaign_name: str
    total_sent: int
    total_opens: int
    total_clicks: int
    total_replies: int
    total_bounces: int
    total_unsubscribes: int
    open_rate: float
    click_rate: float
    reply_rate: float
    bounce_rate: float
    unsubscribe_rate: float
    daily_stats: Optional[List[AnalyticsDaily]]
