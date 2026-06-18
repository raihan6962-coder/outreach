from uuid import UUID
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.warmup import WarmupProgress
from app.models.gmail import GmailAccount
from app.utils.gmail_client import GmailClient


class WarmupService:
    WARMUP_SCHEDULE = [5, 10, 15, 25, 40, 60, 80, 100, 120, 150, 180, 200, 250, 300, 350, 400, 450, 500]

    @staticmethod
    async def get_status(db: AsyncSession, gmail_account_id: UUID) -> dict:
        account = await db.execute(
            select(GmailAccount).where(GmailAccount.id == gmail_account_id)
        )
        gmail_account = account.scalar_one_or_none()
        if not gmail_account:
            raise ValueError("Gmail account not found")

        result = await db.execute(
            select(WarmupProgress)
            .where(WarmupProgress.gmail_account_id == gmail_account_id)
            .order_by(WarmupProgress.date.desc())
            .limit(30)
        )
        history = list(result.scalars().all())

        warmup_result = await db.execute(
            select(WarmupProgress)
            .where(WarmupProgress.gmail_account_id == gmail_account_id)
            .order_by(WarmupProgress.date.desc())
            .limit(1)
        )
        latest = warmup_result.scalar_one_or_none()

        current_level = latest.current_daily if latest else 0
        target = latest.target_daily if latest else gmail_account.warmup_target or 50
        progress = round((current_level / target) * 100, 2) if target > 0 else 0

        return {
            "gmail_account_id": str(gmail_account_id),
            "email": gmail_account.email,
            "current_level": current_level,
            "target_daily": target,
            "progress_percent": progress,
            "is_warming_up": gmail_account.is_warming_up,
            "days_completed": len(history),
            "history": [
                {
                    "date": str(h.date),
                    "sent": h.sent_count,
                    "inbox_rate": h.inbox_rate,
                    "spam_rate": h.spam_rate,
                }
                for h in history
            ],
        }

    @staticmethod
    async def configure(
        db: AsyncSession, gmail_account_id: UUID, target_daily: int
    ) -> WarmupProgress:
        account_result = await db.execute(
            select(GmailAccount).where(GmailAccount.id == gmail_account_id)
        )
        gmail_account = account_result.scalar_one_or_none()
        if not gmail_account:
            raise ValueError("Gmail account not found")

        gmail_account.is_warming_up = True
        gmail_account.warmup_target = target_daily

        progress = WarmupProgress(
            gmail_account_id=gmail_account_id,
            date=datetime.utcnow().date(),
            target_daily=target_daily,
            current_daily=0,
            sent_count=0,
            inbox_rate=0.0,
            spam_rate=0.0,
        )
        db.add(progress)
        await db.commit()
        await db.refresh(progress)
        return progress

    @staticmethod
    async def get_progress(db: AsyncSession, gmail_account_id: UUID) -> list:
        result = await db.execute(
            select(WarmupProgress)
            .where(WarmupProgress.gmail_account_id == gmail_account_id)
            .order_by(WarmupProgress.date.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def process_warmup_step(
        db: AsyncSession, gmail_account_id: UUID
    ) -> bool:
        account_result = await db.execute(
            select(GmailAccount).where(GmailAccount.id == gmail_account_id)
        )
        gmail_account = account_result.scalar_one_or_none()
        if not gmail_account or not gmail_account.is_warming_up:
            return False

        result = await db.execute(
            select(WarmupProgress)
            .where(WarmupProgress.gmail_account_id == gmail_account_id)
            .order_by(WarmupProgress.date.desc())
            .limit(1)
        )
        latest = result.scalar_one_or_none()

        target = gmail_account.warmup_target or 50
        current_level = latest.current_daily if latest else 0
        next_level = WarmupService.get_warmup_schedule(current_level, target)

        if next_level <= current_level:
            return False

        today = datetime.utcnow().date()
        progress_result = await db.execute(
            select(WarmupProgress).where(
                WarmupProgress.gmail_account_id == gmail_account_id,
                WarmupProgress.date == today,
            )
        )
        today_progress = progress_result.scalar_one_or_none()
        if not today_progress:
            today_progress = WarmupProgress(
                gmail_account_id=gmail_account_id,
                date=today,
                target_daily=target,
                current_daily=current_level,
                sent_count=0,
                inbox_rate=0.0,
                spam_rate=0.0,
            )
            db.add(today_progress)
            await db.flush()

        client = GmailClient(gmail_account)
        sent = 0
        for _ in range(next_level - current_level):
            try:
                client.send_warmup_email()
                sent += 1
            except Exception:
                break

        today_progress.current_daily = next_level
        today_progress.sent_count = (today_progress.sent_count or 0) + sent
        inbox_rate = WarmupService.calculate_health_score(db, gmail_account_id)
        today_progress.inbox_rate = inbox_rate
        today_progress.spam_rate = 100 - inbox_rate
        gmail_account.daily_sent += sent
        gmail_account.total_sent = (gmail_account.total_sent or 0) + sent

        if next_level >= target:
            gmail_account.is_warming_up = False

        await db.commit()
        return True

    @staticmethod
    async def calculate_health_score(db: AsyncSession, gmail_account_id: UUID) -> float:
        result = await db.execute(
            select(WarmupProgress)
            .where(WarmupProgress.gmail_account_id == gmail_account_id)
            .order_by(WarmupProgress.date.desc())
            .limit(7)
        )
        recent = list(result.scalars().all())
        if not recent:
            return 100.0

        inbox_rates = [p.inbox_rate for p in recent if p.inbox_rate is not None]
        if not inbox_rates:
            return 100.0
        return sum(inbox_rates) / len(inbox_rates)

    @staticmethod
    def get_warmup_schedule(current_level: int, target: int) -> int:
        for level in sorted(WarmupService.WARMUP_SCHEDULE):
            if level > current_level:
                if level >= target:
                    return target
                return level
        return target
