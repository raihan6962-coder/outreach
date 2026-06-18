from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any


class LeadCreate(BaseModel):
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    source: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class LeadBulkCreate(BaseModel):
    leads: List[LeadCreate]


class LeadResponse(BaseModel):
    id: UUID
    user_id: UUID
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    company: Optional[str]
    title: Optional[str]
    phone: Optional[str]
    linkedin_url: Optional[str]
    website: Optional[str]
    location: Optional[str]
    source: Optional[str]
    custom_fields: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    is_enriched: bool
    enrichment_data: Optional[Dict[str, Any]]
    score: Optional[int]
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class LeadUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    source: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None
    score: Optional[int] = None


class LeadSearchParams(BaseModel):
    query: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    score_min: Optional[int] = None
    score_max: Optional[int] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"
    page: int = 1
    page_size: int = 50


class LeadListResponse(BaseModel):
    items: List[LeadResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class LeadPaginatedResponse(BaseModel):
    items: List[LeadResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
