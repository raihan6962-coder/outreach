from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from app.models.gmail import GmailAccount
from app.models.campaign import CampaignGmailAccount


class RotationService:
    @staticmethod
    async def get_optimal_account(
        db: AsyncSession, campaign_id: UUID
    ) -> GmailAccount:
        result = await db.execute(
            select(CampaignGmailAccount)
            .options(selectinload(CampaignGmailAccount.gmail_account))
            .where(CampaignGmailAccount.campaign_id == campaign_id)
            .order_by(CampaignGmailAccount.order)
        )
        campaign_accounts = list(result.scalars().all())
        if not campaign_accounts:
            raise ValueError("No Gmail accounts linked to campaign")

        eligible = [
            cga.gmail_account
            for cga in campaign_accounts
            if cga.gmail_account.is_active
            and RotationService.check_limits(cga.gmail_account)
        ]

        if not eligible:
            raise ValueError("No eligible Gmail accounts with capacity")

        eligible.sort(key=lambda a: (
            a.daily_sent / a.daily_limit if a.daily_limit > 0 else 1,
            a.hourly_sent / a.hourly_limit if a.hourly_limit > 0 else 1,
        ))
        return eligible[0]

    @staticmethod
    async def update_account_usage(
        db: AsyncSession, account_id: UUID
    ) -> None:
        now = datetime.utcnow()
        result = await db.execute(
            select(GmailAccount).where(GmailAccount.id == account_id)
        )
        account = result.scalar_one_or_none()
        if not account:
            raise ValueError("Gmail account not found")

        if account.last_daily_reset is None or account.last_daily_reset.date() < now.date():
            account.daily_sent = 0
            account.last_daily_reset = now

        if account.last_hourly_reset is None or account.last_hourly_reset.hour != now.hour:
            account.hourly_sent = 0
            account.last_hourly_reset = now

        account.daily_sent += 1
        account.hourly_sent += 1
        account.total_sent = (account.total_sent or 0) + 1
        await db.commit()

    @staticmethod
    async def reset_daily_counts(db: AsyncSession) -> None:
        now = datetime.utcnow()
        await db.execute(
            update(GmailAccount)
            .values(daily_sent=0, last_daily_reset=now)
        )
        await db.commit()

    @staticmethod
    async def reset_hourly_counts(db: AsyncSession) -> None:
        now = datetime.utcnow()
        await db.execute(
            update(GmailAccount)
            .values(hourly_sent=0, last_hourly_reset=now)
        )
        await db.commit()

    @staticmethod
    def check_limits(account: GmailAccount) -> bool:
        if not account.is_active:
            return False
        if account.daily_limit > 0 and account.daily_sent >= account.daily_limit:
            return False
        if account.hourly_limit > 0 and account.hourly_sent >= account.hourly_limit:
            return False
        return True
