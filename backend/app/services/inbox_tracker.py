from uuid import UUID
import re
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.gmail import GmailAccount
from app.models.email_message import EmailMessage
from app.models.email_reply import EmailReply
from app.models.campaign import CampaignLead
from app.utils.gmail_client import GmailClient


class InboxTracker:
    @staticmethod
    async def check_inbox(
        db: AsyncSession, user_id: UUID, account_id: UUID
    ) -> list:
        result = await db.execute(
            select(GmailAccount).where(
                GmailAccount.id == account_id,
                GmailAccount.user_id == user_id,
            )
        )
        account = result.scalar_one_or_none()
        if not account:
            raise ValueError("Gmail account not found")

        client = GmailClient(account)
        messages = client.read_inbox(max_results=20)
        replies = []
        for msg in messages:
            if msg.get("in_reply_to"):
                reply_data = InboxTracker.classify_reply(
                    msg.get("body", ""),
                    msg.get("subject", ""),
                )
                processed = await InboxTracker.process_reply(
                    db, msg.get("message_id"), {**msg, "classification": reply_data}
                )
                replies.append(processed)
        return replies

    @staticmethod
    def classify_reply(message_body: str, subject: str) -> str:
        body_lower = message_body.lower()
        subject_lower = subject.lower()

        if re.search(r"(returned mail|undelivered|delivery failure|mail delivery failed)", body_lower):
            return "bounce"

        if re.search(r"(out of office|auto-reply|automatic reply|vacation|away from)", body_lower):
            return "ooo"

        if re.search(r"(autoreply|auto-reply|auto reply)", subject_lower):
            return "autoreply"

        if re.search(r"(unsubscribe|remove|opt.out|don't email|no more)", body_lower):
            return "not_interested"

        if re.search(r"(interested|pricing|demo|quote|tell me more|schedule|call|meeting)", body_lower):
            return "interested"

        if re.search(r"^(re|fwd)", subject_lower):
            return "reply"

        return "reply"

    @staticmethod
    async def process_reply(
        db: AsyncSession, email_message_id: str, reply_data: dict
    ) -> EmailReply:
        result = await db.execute(
            select(EmailMessage).where(
                EmailMessage.message_id == email_message_id
            )
        )
        email_message = result.scalar_one_or_none()
        if not email_message:
            email_message = EmailMessage(
                message_id=email_message_id,
                subject=reply_data.get("subject", ""),
                from_email=reply_data.get("from", ""),
                body=reply_data.get("body", ""),
            )
            db.add(email_message)
            await db.flush()

        email_message.status = "replied"
        email_message.replied_at = datetime.utcnow()

        classification = reply_data.get("classification", "reply")

        existing_reply = await db.execute(
            select(EmailReply).where(
                EmailReply.message_id == email_message.id
            )
        )
        reply = existing_reply.scalar_one_or_none()
        if not reply:
            reply = EmailReply(
                message_id=email_message.id,
                from_email=reply_data.get("from", ""),
                subject=reply_data.get("subject", ""),
                body=reply_data.get("body", ""),
                classification=classification,
            )
            db.add(reply)
            await db.flush()

        campaign_lead_result = await db.execute(
            select(CampaignLead).where(
                CampaignLead.message_id == email_message_id
            )
        )
        campaign_lead = campaign_lead_result.scalar_one_or_none()
        if campaign_lead:
            campaign_lead.replied_at = datetime.utcnow()
            campaign_lead.status = "replied"

        await db.commit()
        await db.refresh(reply)
        return reply

    @staticmethod
    async def check_bounces(db: AsyncSession, user_id: UUID) -> list:
        result = await db.execute(
            select(GmailAccount).where(
                GmailAccount.user_id == user_id,
                GmailAccount.is_active == True,
            )
        )
        accounts = list(result.scalars().all())
        bounces = []
        for account in accounts:
            client = GmailClient(account)
            messages = client.read_inbox(max_results=50)
            for msg in messages:
                classification = InboxTracker.classify_reply(
                    msg.get("body", ""), msg.get("subject", "")
                )
                if classification == "bounce":
                    bounces.append({
                        "account_id": str(account.id),
                        "message_id": msg.get("message_id"),
                        "subject": msg.get("subject"),
                        "body": msg.get("body"),
                    })
                    email_msg = EmailMessage(
                        message_id=msg.get("message_id"),
                        subject=msg.get("subject", ""),
                        from_email=msg.get("from", ""),
                        body=msg.get("body", ""),
                        status="bounced",
                    )
                    db.add(email_msg)
                    await db.flush()
                    campaign_lead_result = await db.execute(
                        select(CampaignLead).where(
                            CampaignLead.message_id == msg.get("message_id")
                        )
                    )
                    campaign_lead = campaign_lead_result.scalar_one_or_none()
                    if campaign_lead:
                        campaign_lead.status = "bounced"
                        campaign_lead.bounced_at = datetime.utcnow()
            await db.commit()
        return bounces

    @staticmethod
    async def check_auto_replies(db: AsyncSession, user_id: UUID) -> list:
        result = await db.execute(
            select(GmailAccount).where(
                GmailAccount.user_id == user_id,
                GmailAccount.is_active == True,
            )
        )
        accounts = list(result.scalars().all())
        auto_replies = []
        for account in accounts:
            client = GmailClient(account)
            messages = client.read_inbox(max_results=50)
            for msg in messages:
                classification = InboxTracker.classify_reply(
                    msg.get("body", ""), msg.get("subject", "")
                )
                if classification in ("ooo", "autoreply"):
                    auto_replies.append({
                        "account_id": str(account.id),
                        "message_id": msg.get("message_id"),
                        "subject": msg.get("subject"),
                        "body": msg.get("body"),
                        "classification": classification,
                    })
                    email_msg = EmailMessage(
                        message_id=msg.get("message_id"),
                        subject=msg.get("subject", ""),
                        from_email=msg.get("from", ""),
                        body=msg.get("body", ""),
                        status=classification,
                    )
                    db.add(email_msg)
        await db.commit()
        return auto_replies
