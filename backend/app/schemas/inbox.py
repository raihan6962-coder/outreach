from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List


class EmailAttachmentResponse(BaseModel):
    id: UUID
    message_id: UUID
    filename: str
    mime_type: str
    size_bytes: int
    storage_path: Optional[str]
    attachment_id: Optional[str]
    model_config = {"from_attributes": True}


class EmailMessageResponse(BaseModel):
    id: UUID
    gmail_account_id: UUID
    thread_id: str
    gmail_message_id: str
    from_header: str
    to_header: str
    cc_header: Optional[str]
    bcc_header: Optional[str]
    subject: Optional[str]
    body_text: Optional[str]
    body_html: Optional[str]
    snippet: Optional[str]
    is_read: bool
    is_starred: bool
    is_trash: bool
    is_spam: bool
    is_reply: bool
    label_ids: Optional[List[str]]
    campaign_id: Optional[UUID]
    lead_id: Optional[UUID]
    attachments: Optional[List[EmailAttachmentResponse]]
    received_at: datetime
    created_at: datetime
    model_config = {"from_attributes": True}


class EmailReplyResponse(BaseModel):
    id: UUID
    original_message_id: UUID
    reply_message_id: UUID
    gmail_account_id: UUID
    lead_id: Optional[UUID]
    campaign_id: Optional[UUID]
    body_text: Optional[str]
    body_html: Optional[str]
    snippet: Optional[str]
    is_automated: bool
    is_positive: Optional[bool]
    sentiment_score: Optional[float]
    received_at: datetime
    created_at: datetime
    model_config = {"from_attributes": True}


class EmailThreadResponse(BaseModel):
    id: UUID
    thread_id: str
    gmail_account_id: UUID
    subject: Optional[str]
    participants: List[str]
    message_count: int
    last_message_at: datetime
    is_read: bool
    is_starred: bool
    labels: Optional[List[str]]
    messages: Optional[List[EmailMessageResponse]]
    created_at: datetime
    model_config = {"from_attributes": True}


class InboxFilter(BaseModel):
    is_read: Optional[bool] = None
    is_starred: Optional[bool] = None
    is_spam: Optional[bool] = None
    is_trash: Optional[bool] = None
    is_reply: Optional[bool] = None
    campaign_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    gmail_account_id: Optional[UUID] = None
    has_attachments: Optional[bool] = None
    label_ids: Optional[List[str]] = None
    from_email: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class InboxSearchParams(BaseModel):
    query: Optional[str] = None
    filters: Optional[InboxFilter] = None
    sort_by: str = "received_at"
    sort_order: str = "desc"
    page: int = 1
    page_size: int = 50


class InboxPaginatedResponse(BaseModel):
    items: List[EmailMessageResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class EmailSendRequest(BaseModel):
    gmail_account_id: UUID
    to: str
    cc: Optional[str] = None
    bcc: Optional[str] = None
    subject: str
    body_html: str
    body_text: Optional[str] = None
    thread_id: Optional[str] = None
    in_reply_to: Optional[UUID] = None
    campaign_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None


class EmailDraftUpdate(BaseModel):
    to: Optional[str] = None
    cc: Optional[str] = None
    bcc: Optional[str] = None
    subject: Optional[str] = None
    body_html: Optional[str] = None
    body_text: Optional[str] = None
