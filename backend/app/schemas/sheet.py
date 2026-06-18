from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any


class SheetColumnMapping(BaseModel):
    sheet_column: str
    lead_field: str
    is_required: bool = False


class SheetSourceCreate(BaseModel):
    name: str
    sheet_id: str
    sheet_name: Optional[str] = None
    sheet_range: Optional[str] = None
    column_mappings: Optional[List[SheetColumnMapping]] = None
    header_row: int = 1
    data_start_row: int = 2
    import_interval_minutes: Optional[int] = None


class SheetSourceResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    sheet_id: str
    sheet_name: Optional[str]
    sheet_range: Optional[str]
    column_mappings: Optional[List[Dict[str, Any]]]
    header_row: int
    data_start_row: int
    import_interval_minutes: Optional[int]
    last_import_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class SheetSourceUpdate(BaseModel):
    name: Optional[str] = None
    sheet_id: Optional[str] = None
    sheet_name: Optional[str] = None
    sheet_range: Optional[str] = None
    column_mappings: Optional[List[SheetColumnMapping]] = None
    header_row: Optional[int] = None
    data_start_row: Optional[int] = None
    import_interval_minutes: Optional[int] = None
    is_active: Optional[bool] = None


class SheetImportRequest(BaseModel):
    sheet_source_id: UUID
    preview_only: bool = False
    max_rows: Optional[int] = None


class SheetImportResponse(BaseModel):
    sheet_source_id: UUID
    total_rows_found: int
    rows_imported: int
    rows_skipped: int
    errors: Optional[List[str]]
    preview: Optional[List[Dict[str, Any]]]
    completed_at: datetime
    model_config = {"from_attributes": True}


class SheetRowResponse(BaseModel):
    id: UUID
    sheet_source_id: UUID
    row_number: int
    data: Dict[str, Any]
    is_imported: bool
    imported_at: Optional[datetime]
    created_at: datetime
    model_config = {"from_attributes": True}
