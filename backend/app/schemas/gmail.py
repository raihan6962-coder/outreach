from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List


class GmailAccountCreate(BaseModel):
    email: str
    access_token: str
    refresh_token: Optional[str] = None
    token_expiry: Optional[datetime] = None
    label_ids: Optional[List[str]] = None


class GmailAccountResponse(BaseModel):
    id: UUID
    user_id: UUID
    email: str
    is_authenticated: bool
    is_active: bool
    is_primary: bool
    label_ids: Optional[List[str]]
    history_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class GmailAccountUpdate(BaseModel):
    is_primary: Optional[bool] = None
    is_active: Optional[bool] = None
    label_ids: Optional[List[str]] = None


class GmailMessageResponse(BaseModel):
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
    is_draft: bool
    label_ids: Optional[List[str]]
    received_at: datetime
    created_at: datetime
    model_config = {"from_attributes": True}


class GmailMessageListResponse(BaseModel):
    items: List[GmailMessageResponse]
    total: int
    page: int
    page_size: int
    next_page_token: Optional[str]


class GmailSendRequest(BaseModel):
    gmail_account_id: UUID
    to: str
    cc: Optional[str] = None
    bcc: Optional[str] = None
    subject: str
    body_html: str
    body_text: Optional[str] = None
    draft_id: Optional[str] = None
    thread_id: Optional[str] = None


class GmailDraftResponse(BaseModel):
    id: UUID
    gmail_account_id: UUID
    gmail_draft_id: Optional[str]
    to: Optional[str]
    cc: Optional[str]
    bcc: Optional[str]
    subject: Optional[str]
    body_html: Optional[str]
    body_text: Optional[str]
    thread_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class GmailLabelResponse(BaseModel):
    id: str
    name: str
    label_type: str
    color: Optional[dict]
    message_list_visibility: Optional[str]
    label_list_visibility: Optional[str]
    model_config = {"from_attributes": True}


class GmailHistoryResponse(BaseModel):
    history_id: str
    messages_added: Optional[List[dict]]
    messages_deleted: Optional[List[dict]]
    labels_added: Optional[List[dict]]
    labels_removed: Optional[List[dict]]
    model_config = {"from_attributes": True}


class GmailWatchRequest(BaseModel):
    gmail_account_id: UUID
    topic_name: str
    label_ids: Optional[List[str]] = None
