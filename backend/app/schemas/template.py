from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any


class TemplateFolderCreate(BaseModel):
    name: str
    parent_id: Optional[UUID] = None
    color: Optional[str] = None


class TemplateFolderResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    parent_id: Optional[UUID]
    color: Optional[str]
    template_count: Optional[int]
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class TemplateFolderUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[UUID] = None
    color: Optional[str] = None


class TemplateCreate(BaseModel):
    name: str
    folder_id: Optional[UUID] = None
    subject: str
    body_html: str
    body_text: Optional[str] = None
    variables: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_shared: bool = False


class TemplateResponse(BaseModel):
    id: UUID
    user_id: UUID
    folder_id: Optional[UUID]
    name: str
    subject: str
    body_html: str
    body_text: Optional[str]
    variables: Optional[List[str]]
    tags: Optional[List[str]]
    is_shared: bool
    version: int
    usage_count: int
    last_used_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    folder_id: Optional[UUID] = None
    subject: Optional[str] = None
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    variables: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_shared: Optional[bool] = None


class TemplateRenderRequest(BaseModel):
    template_id: UUID
    variables: Dict[str, Any]


class TemplateRenderResponse(BaseModel):
    subject: str
    body_html: str
    body_text: Optional[str]
    used_variables: List[str]
