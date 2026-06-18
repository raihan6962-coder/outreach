from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.schemas import NotificationResponse
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get("/", response_model=list[NotificationResponse])
async def list_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    notifications = await NotificationService.get_notifications(db, current_user.id)
    return [
        NotificationResponse(
            id=n.id,
            user_id=n.user_id,
            title=n.title,
            message=n.message,
            notification_type=n.type,
            severity="info",
            is_read=n.is_read,
            is_dismissed=False,
            action_url=None,
            metadata=None,
            created_at=n.created_at,
            read_at=n.read_at if hasattr(n, "read_at") else None,
        )
        for n in notifications
    ]


@router.put("/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await NotificationService.mark_read(db, notification_id)
        return {"message": "Marked as read"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await NotificationService.mark_all_read(db, current_user.id)
    return {"message": "All marked as read"}


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await NotificationService.get_unread_count(db, current_user.id)
    return {"count": count}
