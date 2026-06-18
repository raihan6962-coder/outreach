from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List


class SpamTestCreate(BaseModel):
    gmail_account_id: UUID
    subject: str
    body_html: str
    body_text: Optional[str] = None
    from_name: Optional[str] = None
    reply_to: Optional[str] = None
    include_links: bool = True
    include_images: bool = False


class SpamTestResponse(BaseModel):
    id: UUID
    user_id: UUID
    gmail_account_id: UUID
    subject: str
    spam_score: float
    spam_level: str
    recommendations: List[str]
    test_details: Optional[dict]
    is_completed: bool
    created_at: datetime
    completed_at: Optional[datetime]
    model_config = {"from_attributes": True}


class SpamTestResultResponse(BaseModel):
    id: UUID
    user_id: UUID
    gmail_account_id: UUID
    subject: str
    spam_score: float
    spam_level: str
    recommendations: List[str]
    word_count: int
    link_count: int
    image_count: int
    has_attachment: bool
    contains_spam_words: bool
    contains_uppercase: bool
    contains_excessive_punctuation: bool
    subject_line_score: float
    content_score: float
    formatting_score: float
    overall_score: float
    test_details: Optional[dict]
    created_at: datetime
    model_config = {"from_attributes": True}


class SpamTestScheduleRequest(BaseModel):
    gmail_account_id: UUID
    schedule_type: str
    interval_hours: Optional[int] = None
    time_of_day: Optional[str] = None
    day_of_week: Optional[int] = None
    is_active: bool = True
