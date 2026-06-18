from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    message: str
    notification_type: str
    severity: str
    is_read: bool
    is_dismissed: bool
    action_url: Optional[str]
    metadata: Optional[dict]
    created_at: datetime
    read_at: Optional[datetime]
    model_config = {"from_attributes": True}


class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None
    is_dismissed: Optional[bool] = None


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int
