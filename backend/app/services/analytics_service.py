from uuid import UUID
from datetime import datetime, timedelta, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.campaign import CampaignLead, Campaign
from app.models.lead import Lead
from app.models.email_validation import EmailValidation
from app.models.email_reply import EmailReply
from app.models.email_message import EmailMessage
from app.models.gmail import GmailAccount


class AnalyticsService:
    @staticmethod
    async def get_overview(db: AsyncSession, user_id: UUID, period: str = "all") -> dict:
        metrics = await AnalyticsService.calculate_metrics(db, user_id)
        return {
            **metrics,
            "period": period,
            "generated_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    async def get_daily_stats(db: AsyncSession, user_id: UUID, days: int = 30) -> list:
        since = datetime.utcnow() - timedelta(days=days)
        result = await db.execute(
            select(
                func.date(CampaignLead.sent_at).label("date"),
                func.count(CampaignLead.id).label("sent"),
                func.sum(
                    func.cast(CampaignLead.status == "replied", func.Integer)
                ).label("replies"),
            )
            .select_from(CampaignLead)
            .join(Campaign, CampaignLead.campaign_id == Campaign.id)
            .where(
                Campaign.user_id == user_id,
                CampaignLead.sent_at >= since,
            )
            .group_by(func.date(CampaignLead.sent_at))
            .order_by(func.date(CampaignLead.sent_at))
        )
        rows = result.all()
        return [
            {
                "date": str(row.date),
                "sent": int(row.sent),
                "replies": int(row.replies or 0),
            }
            for row in rows
        ]

    @staticmethod
    async def get_weekly_stats(db: AsyncSession, user_id: UUID, weeks: int = 12) -> list:
        since = datetime.utcnow() - timedelta(weeks=weeks)
        result = await db.execute(
            select(
                func.strftime("%Y-%W", CampaignLead.sent_at).label("week"),
                func.count(CampaignLead.id).label("sent"),
                func.sum(
                    func.cast(CampaignLead.status == "replied", func.Integer)
                ).label("replies"),
            )
            .select_from(CampaignLead)
            .join(Campaign, CampaignLead.campaign_id == Campaign.id)
            .where(
                Campaign.user_id == user_id,
                CampaignLead.sent_at >= since,
            )
            .group_by(func.strftime("%Y-%W", CampaignLead.sent_at))
            .order_by(func.strftime("%Y-%W", CampaignLead.sent_at))
        )
        rows = result.all()
        return [
            {"week": row.week, "sent": int(row.sent), "replies": int(row.replies or 0)}
            for row in rows
        ]

    @staticmethod
    async def get_monthly_stats(db: AsyncSession, user_id: UUID, months: int = 12) -> list:
        since = datetime.utcnow() - timedelta(days=months * 30)
        result = await db.execute(
            select(
                func.strftime("%Y-%m", CampaignLead.sent_at).label("month"),
                func.count(CampaignLead.id).label("sent"),
                func.sum(
                    func.cast(CampaignLead.status == "replied", func.Integer)
                ).label("replies"),
            )
            .select_from(CampaignLead)
            .join(Campaign, CampaignLead.campaign_id == Campaign.id)
            .where(
                Campaign.user_id == user_id,
                CampaignLead.sent_at >= since,
            )
            .group_by(func.strftime("%Y-%m", CampaignLead.sent_at))
            .order_by(func.strftime("%Y-%m", CampaignLead.sent_at))
        )
        rows = result.all()
        return [
            {
                "month": row.month,
                "sent": int(row.sent),
                "replies": int(row.replies or 0),
            }
            for row in rows
        ]

    @staticmethod
    async def get_gmail_health(db: AsyncSession, user_id: UUID) -> list:
        result = await db.execute(
            select(GmailAccount).where(GmailAccount.user_id == user_id)
        )
        accounts = list(result.scalars().all())
        return [
            {
                "id": str(acc.id),
                "email": acc.email,
                "is_active": acc.is_active,
                "daily_sent": acc.daily_sent,
                "daily_limit": acc.daily_limit,
                "hourly_sent": acc.hourly_sent,
                "hourly_limit": acc.hourly_limit,
                "total_sent": acc.total_sent or 0,
                "health_score": round(
                    (1 - (acc.daily_sent / acc.daily_limit if acc.daily_limit > 0 else 0))
                    * 100,
                    2,
                ),
            }
            for acc in accounts
        ]

    @staticmethod
    async def calculate_metrics(db: AsyncSession, user_id: UUID) -> dict:
        leads_result = await db.execute(
            select(func.count()).select_from(Lead).where(Lead.user_id == user_id)
        )
        total_leads = leads_result.scalar() or 0

        campaigns_result = await db.execute(
            select(Campaign).where(Campaign.user_id == user_id)
        )
        campaigns = list(campaigns_result.scalars().all())
        campaign_ids = [c.id for c in campaigns]

        if not campaign_ids:
            return {
                "total_leads": total_leads,
                "emails_sent": 0,
                "valid_emails": 0,
                "invalid_emails": 0,
                "inbox_rate": 0,
                "spam_rate": 0,
                "open_rate": 0,
                "reply_rate": 0,
                "positive_reply_rate": 0,
                "bounce_rate": 0,
                "gmail_health_score": 0,
            }

        sent_result = await db.execute(
            select(func.count()).select_from(CampaignLead).where(
                CampaignLead.campaign_id.in_(campaign_ids),
                CampaignLead.status == "sent",
            )
        )
        emails_sent = sent_result.scalar() or 0

        valid_result = await db.execute(
            select(func.count()).select_from(EmailValidation).join(
                Lead, EmailValidation.lead_id == Lead.id
            ).where(
                Lead.user_id == user_id,
                EmailValidation.is_valid == True,
            )
        )
        valid_emails = valid_result.scalar() or 0

        invalid_result = await db.execute(
            select(func.count()).select_from(EmailValidation).join(
                Lead, EmailValidation.lead_id == Lead.id
            ).where(
                Lead.user_id == user_id,
                EmailValidation.is_valid == False,
            )
        )
        invalid_emails = invalid_result.scalar() or 0

        replied_result = await db.execute(
            select(func.count()).select_from(CampaignLead).where(
                CampaignLead.campaign_id.in_(campaign_ids),
                CampaignLead.replied_at.isnot(None),
            )
        )
        replies = replied_result.scalar() or 0

        bounced_result = await db.execute(
            select(func.count()).select_from(CampaignLead).where(
                CampaignLead.campaign_id.in_(campaign_ids),
                CampaignLead.status == "bounced",
            )
        )
        bounces = bounced_result.scalar() or 0

        positive_replies_result = await db.execute(
            select(func.count()).select_from(EmailReply).where(
                EmailReply.classification == "interested"
            )
        )
        positive_replies = positive_replies_result.scalar() or 0

        gmail_result = await db.execute(
            select(GmailAccount).where(GmailAccount.user_id == user_id)
        )
        gmail_accounts = list(gmail_result.scalars().all())
        if gmail_accounts:
            gmail_health_score = round(
                sum(
                    (1 - (a.daily_sent / a.daily_limit if a.daily_limit > 0 else 0))
                    * 100
                    for a in gmail_accounts
                )
                / len(gmail_accounts),
                2,
            )
        else:
            gmail_health_score = 0

        return {
            "total_leads": total_leads,
            "emails_sent": emails_sent,
            "valid_emails": valid_emails,
            "invalid_emails": invalid_emails,
            "inbox_rate": round(
                (emails_sent - bounces) / emails_sent * 100 if emails_sent else 0, 2
            ),
            "spam_rate": round(
                bounces / emails_sent * 100 if emails_sent else 0, 2
            ),
            "open_rate": 0,
            "reply_rate": round(
                replies / emails_sent * 100 if emails_sent else 0, 2
            ),
            "positive_reply_rate": round(
                positive_replies / replies * 100 if replies else 0, 2
            ),
            "bounce_rate": round(
                bounces / emails_sent * 100 if emails_sent else 0, 2
            ),
            "gmail_health_score": gmail_health_score,
        }
