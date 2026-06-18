from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID
from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.schemas import (
    TemplateCreate, TemplateResponse, TemplateUpdate,
    TemplateFolderCreate, TemplateFolderResponse,
)
from app.services.template_service import TemplateService

router = APIRouter()


class TemplatePreviewRequest(BaseModel):
    variables: Dict[str, Any]


class TemplatePreviewResponse(BaseModel):
    subject: str
    body_html: str
    body_text: Optional[str] = None


class TemplateTestSendRequest(BaseModel):
    test_email: str
    variables: Dict[str, Any] = {}


@router.get("/", response_model=list[TemplateResponse])
async def list_templates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    templates = await TemplateService.get_templates(db, current_user.id)
    return templates


@router.post("/", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: TemplateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    template = await TemplateService.create_template(db, current_user.id, data)
    return template


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        template = await TemplateService.get_template(db, template_id)
        return template
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: UUID,
    data: TemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        template = await TemplateService.update_template(db, template_id, data)
        return template
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{template_id}")
async def delete_template(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await TemplateService.delete_template(db, template_id)
        return {"message": "Deleted"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{template_id}/duplicate", response_model=TemplateResponse)
async def duplicate_template(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        template = await TemplateService.duplicate_template(db, template_id)
        return template
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{template_id}/preview", response_model=TemplatePreviewResponse)
async def preview_template(
    template_id: UUID,
    data: TemplatePreviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        rendered = await TemplateService.preview_template(db, template_id, data.variables)
        return TemplatePreviewResponse(
            subject=rendered["subject"],
            body_html=rendered["body_html"],
            body_text=rendered.get("body_text"),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{template_id}/test-send")
async def test_send_template(
    template_id: UUID,
    data: TemplateTestSendRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await TemplateService.test_send(db, current_user.id, template_id, data.test_email, data.variables)
        return {"message": "Test email sent"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/folders", response_model=TemplateFolderResponse, status_code=status.HTTP_201_CREATED)
async def create_folder(
    data: TemplateFolderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    folder = await TemplateService.create_folder(db, current_user.id, data.name)
    return folder


@router.get("/folders", response_model=list[TemplateFolderResponse])
async def list_folders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    folders = await TemplateService.get_folders(db, current_user.id)
    return folders
