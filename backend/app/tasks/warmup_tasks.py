import asyncio
from uuid import UUID
from datetime import datetime, timezone, date as date_type
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.tasks.celery_app import celery_app
from app.database import async_session_maker
from app.models.gmail_account import GmailAccount
from app.models.warmup import WarmupProgress
from app.utils.gmail_client import GmailClient


WARMUP_SCHEDULE = [5, 10, 15, 25, 40, 60, 80, 100, 120, 150, 180, 200, 250, 300, 350, 400, 450, 500]


def run_async(coro):
    return asyncio.run(coro)


def _get_next_level(current: int, target: int) -> int:
    for level in sorted(WARMUP_SCHEDULE):
        if level > current:
            return min(level, target)
    return target


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_warmup(self, account_id: str):
    async def _run():
        async with async_session_maker() as db:
            result = await db.execute(
                select(GmailAccount).where(GmailAccount.id == UUID(account_id))
            )
            account = result.scalar_one_or_none()
            if not account:
                raise ValueError(f"GmailAccount {account_id} not found")

            if account.warmup_status != "active":
                return {"account_id": account_id, "status": "not_in_warmup"}

            progress_result = await db.execute(
                select(WarmupProgress)
                .where(WarmupProgress.gmail_account_id == account.id)
                .order_by(WarmupProgress.date.desc())
                .limit(1)
            )
            latest = progress_result.scalar_one_or_none()

            current_level = latest.target_count if latest else 0
            target = account.daily_limit

            next_level = _get_next_level(current_level, target)
            if next_level <= current_level:
                return {"account_id": account_id, "status": "already_at_target", "level": current_level}

            today = datetime.now(timezone.utc).date()
            today_progress_result = await db.execute(
                select(WarmupProgress).where(
                    WarmupProgress.gmail_account_id == account.id,
                    WarmupProgress.date == today,
                )
            )
            today_progress = today_progress_result.scalar_one_or_none()

            if not today_progress:
                today_progress = WarmupProgress(
                    gmail_account_id=account.id,
                    date=today,
                    target_count=next_level,
                    sent_count=0,
                    inbox_count=0,
                    spam_count=0,
                    reply_count=0,
                )
                db.add(today_progress)
                await db.flush()

            client = GmailClient(account)
            sent_in_step = 0
            for _ in range(next_level - current_level):
                try:
                    client.send_email(
                        to=account.email,
                        subject=f"Warmup {sent_in_step + 1}",
                        body_html="<p>Warmup message</p>",
                        body_text="Warmup message",
                    )
                    sent_in_step += 1
                except Exception:
                    break

            today_progress.target_count = next_level
            today_progress.sent_count = (today_progress.sent_count or 0) + sent_in_step
            account.daily_sent = (account.daily_sent or 0) + sent_in_step
            account.warmup_progress = int((next_level / target) * 100) if target > 0 else 0

            if next_level >= target:
                account.warmup_status = "completed"

            await db.commit()
            return {
                "account_id": account_id,
                "level": next_level,
                "target": target,
                "sent_in_step": sent_in_step,
                "status": account.warmup_status,
            }

    try:
        return run_async(_run())
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task
def process_warmup_all():
    async def _run():
        async with async_session_maker() as db:
            result = await db.execute(
                select(GmailAccount).where(GmailAccount.warmup_status == "active")
            )
            accounts = list(result.scalars().all())

        results = []
        for account in accounts:
            try:
                res = process_warmup.delay(str(account.id))
                results.append({"account_id": str(account.id), "task_id": res.id})
            except Exception as e:
                results.append({"account_id": str(account.id), "error": str(e)})
        return {"processed": len(results), "results": results}

    return run_async(_run())
