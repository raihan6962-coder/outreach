from uuid import UUID
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from app.models.notification import Notification
from app.models.campaign import Campaign
from app.models.gmail import GmailAccount
from app.models.email_reply import EmailReply
from app.models.email_message import EmailMessage
from app.models.spam_test import SpamTest


class NotificationService:
    @staticmethod
    async def create_notification(
        db: AsyncSession,
        user_id: UUID,
        type: str,
        title: str,
        message: str,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            is_read=False,
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification

    @staticmethod
    async def get_notifications(
        db: AsyncSession, user_id: UUID, limit: int = 50
    ) -> list:
        result = await db.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_unread_count(db: AsyncSession, user_id: UUID) -> int:
        result = await db.execute(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
        )
        return result.scalar() or 0

    @staticmethod
    async def mark_read(
        db: AsyncSession, notification_id: UUID
    ) -> bool:
        result = await db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notification = result.scalar_one_or_none()
        if not notification:
            raise ValueError("Notification not found")
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        await db.commit()
        return True

    @staticmethod
    async def mark_all_read(db: AsyncSession, user_id: UUID) -> bool:
        await db.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
            .values(is_read=True, read_at=datetime.utcnow())
        )
        await db.commit()
        return True

    @staticmethod
    async def notify_campaign_finished(
        db: AsyncSession, campaign: Campaign
    ) -> Notification:
        return await NotificationService.create_notification(
            db,
            user_id=campaign.user_id,
            type="campaign_finished",
            title=f"Campaign '{campaign.name}' completed",
            message=f"All leads have been processed. Total sent: {campaign.lead_count}",
        )

    @staticmethod
    async def notify_gmail_limit(
        db: AsyncSession, gmail_account: GmailAccount
    ) -> Notification:
        return await NotificationService.create_notification(
            db,
            user_id=gmail_account.user_id,
            type="gmail_limit",
            title="Gmail daily limit reached",
            message=f"Account {gmail_account.email} has reached its daily sending limit",
        )

    @staticmethod
    async def notify_gmail_disconnected(
        db: AsyncSession, gmail_account: GmailAccount
    ) -> Notification:
        return await NotificationService.create_notification(
            db,
            user_id=gmail_account.user_id,
            type="gmail_disconnected",
            title="Gmail account disconnected",
            message=f"Account {gmail_account.email} has been disconnected and needs reauthorization",
        )

    @staticmethod
    async def notify_new_reply(
        db: AsyncSession, reply: EmailReply
    ) -> Notification:
        message_result = await db.execute(
            select(EmailMessage).where(EmailMessage.id == reply.message_id)
        )
        email_message = message_result.scalar_one_or_none()
        user_id = email_message.user_id if email_message else None
        return await NotificationService.create_notification(
            db,
            user_id=user_id,
            type="new_reply",
            title="New reply received",
            message=f"New reply from {reply.from_email}: {reply.subject}",
        )

    @staticmethod
    async def notify_bounce(
        db: AsyncSession, email_message: EmailMessage
    ) -> Notification:
        return await NotificationService.create_notification(
            db,
            user_id=email_message.user_id if hasattr(email_message, 'user_id') else None,
            type="bounce",
            title="Email bounced",
            message=f"Email to {email_message.from_email} bounced: {email_message.subject}",
        )

    @staticmethod
    async def notify_spam_risk(
        db: AsyncSession, spam_test: SpamTest
    ) -> Notification:
        return await NotificationService.create_notification(
            db,
            user_id=spam_test.user_id,
            type="spam_risk",
            title="Spam risk detected",
            message=f"Email content scored {spam_test.spam_score}/100 spam score. Review recommended.",
        )
