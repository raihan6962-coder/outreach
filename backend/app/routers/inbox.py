from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.models.email_message import EmailMessage
from app.models.email_reply import EmailReply
from app.models.gmail import GmailAccount
from app.schemas import EmailMessageResponse, EmailReplyResponse, InboxFilter
from app.services.inbox_tracker import InboxTracker

router = APIRouter()


class ThreadSummary(BaseModel):
    thread_id: str
    gmail_account_id: UUID
    subject: str
    participants: List[str]
    message_count: int
    last_message_at: datetime
    is_read: bool


@router.get("/")
async def list_messages(
    gmail_account_id: Optional[UUID] = Query(None),
    is_read: Optional[bool] = Query(None),
    is_reply: Optional[bool] = Query(None),
    campaign_id: Optional[UUID] = Query(None),
    lead_id: Optional[UUID] = Query(None),
    from_email: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(EmailMessage)
        .join(GmailAccount, EmailMessage.gmail_account_id == GmailAccount.id)
        .where(GmailAccount.user_id == current_user.id)
    )
    if gmail_account_id:
        query = query.where(EmailMessage.gmail_account_id == gmail_account_id)
    if is_read is not None:
        query = query.where(EmailMessage.status != "pending" if is_read else EmailMessage.status == "pending")
    if campaign_id:
        query = query.where(EmailMessage.campaign_id == campaign_id)
    if from_email:
        query = query.where(EmailMessage.from_email.ilike(f"%{from_email}%"))
    if date_from:
        query = query.where(EmailMessage.received_at >= date_from)
    if date_to:
        query = query.where(EmailMessage.received_at <= date_to)
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    query = query.order_by(EmailMessage.received_at.desc())
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    messages = list(result.scalars().all())
    total_pages = max(1, (total + page_size - 1) // page_size)
    return {
        "items": [EmailMessageResponse.model_validate(m) for m in messages],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }


@router.get("/{message_id}", response_model=EmailMessageResponse)
async def get_message(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EmailMessage)
        .join(GmailAccount, EmailMessage.gmail_account_id == GmailAccount.id)
        .where(EmailMessage.id == message_id, GmailAccount.user_id == current_user.id)
        .options(selectinload(EmailMessage.email_replies))
    )
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return message


@router.get("/{message_id}/replies", response_model=list[EmailReplyResponse])
async def get_message_replies(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EmailMessage)
        .join(GmailAccount, EmailMessage.gmail_account_id == GmailAccount.id)
        .where(EmailMessage.id == message_id, GmailAccount.user_id == current_user.id)
    )
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    replies_result = await db.execute(
        select(EmailReply)
        .where(EmailReply.email_message_id == message_id)
        .order_by(EmailReply.received_at.asc())
    )
    return list(replies_result.scalars().all())


@router.put("/{message_id}/classify", response_model=EmailReplyResponse)
async def classify_message(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EmailMessage)
        .join(GmailAccount, EmailMessage.gmail_account_id == GmailAccount.id)
        .where(EmailMessage.id == message_id, GmailAccount.user_id == current_user.id)
    )
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    classification = InboxTracker.classify_reply(
        message.body or "", message.subject or ""
    )
    existing = await db.execute(
        select(EmailReply).where(EmailReply.email_message_id == message_id)
    )
    reply = existing.scalar_one_or_none()
    if reply:
        reply.reply_type = classification
        await db.commit()
        await db.refresh(reply)
        return reply
    reply = EmailReply(
        email_message_id=message.id,
        gmail_account_id=message.gmail_account_id,
        from_email=message.from_email,
        subject=message.subject,
        reply_type=classification,
    )
    db.add(reply)
    await db.commit()
    await db.refresh(reply)
    return reply


@router.get("/stats")
async def get_inbox_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    total = await db.execute(
        select(func.count()).select_from(EmailMessage)
        .join(GmailAccount, EmailMessage.gmail_account_id == GmailAccount.id)
        .where(GmailAccount.user_id == current_user.id)
    )
    total_count = total.scalar() or 0
    unread = await db.execute(
        select(func.count()).select_from(EmailMessage)
        .join(GmailAccount, EmailMessage.gmail_account_id == GmailAccount.id)
        .where(GmailAccount.user_id == current_user.id, EmailMessage.status == "pending")
    )
    unread_count = unread.scalar() or 0
    replies = await db.execute(
        select(func.count()).select_from(EmailReply)
        .join(GmailAccount, EmailReply.gmail_account_id == GmailAccount.id)
        .where(GmailAccount.user_id == current_user.id)
    )
    reply_count = replies.scalar() or 0
    return {
        "total_messages": total_count,
        "unread_count": unread_count,
        "total_replies": reply_count,
        "read_count": total_count - unread_count,
    }


@router.get("/threads", response_model=list[dict])
async def get_threads(
    gmail_account_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(EmailMessage.thread_id, func.count().label("message_count"), func.max(EmailMessage.received_at).label("last_message_at"))
        .join(GmailAccount, EmailMessage.gmail_account_id == GmailAccount.id)
        .where(GmailAccount.user_id == current_user.id)
    )
    if gmail_account_id:
        query = query.where(EmailMessage.gmail_account_id == gmail_account_id)
    query = query.group_by(EmailMessage.thread_id).order_by(func.max(EmailMessage.received_at).desc())
    result = await db.execute(query)
    rows = result.all()
    threads = []
    for row in rows:
        first_msg = await db.execute(
            select(EmailMessage)
            .where(EmailMessage.thread_id == row.thread_id)
            .order_by(EmailMessage.received_at.asc())
            .limit(1)
        )
        first = first_msg.scalar_one_or_none()
        threads.append({
            "thread_id": row.thread_id,
            "subject": first.subject if first else "",
            "participants": [first.from_email] if first else [],
            "message_count": row.message_count,
            "last_message_at": row.last_message_at,
            "is_read": True,
        })
    return threads
