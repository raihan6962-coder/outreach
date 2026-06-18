import asyncio
from uuid import UUID
from sqlalchemy import select

from app.tasks.celery_app import celery_app
from app.database import async_session_maker
from app.models.sheet_source import SheetSource
from app.services.google_sheet_service import GoogleSheetService


def run_async(coro):
    return asyncio.run(coro)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def fetch_sheet_leads(self, source_id: str):
    async def _run():
        async with async_session_maker() as db:
            result = await db.execute(
                select(SheetSource).where(SheetSource.id == UUID(source_id))
            )
            sheet_source = result.scalar_one_or_none()
            if not sheet_source:
                raise ValueError(f"SheetSource {source_id} not found")

            count = await GoogleSheetService.fetch_pending_leads(db, sheet_source, sheet_source.user_id)
            sheet_source.last_fetched_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
            await db.commit()
            return {"source_id": source_id, "leads_fetched": count}

    try:
        return run_async(_run())
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task
def fetch_all_sheet_leads():
    async def _run():
        async with async_session_maker() as db:
            result = await db.execute(
                select(SheetSource).where(SheetSource.is_active == True)
            )
            sources = list(result.scalars().all())

        results = []
        for source in sources:
            try:
                res = fetch_sheet_leads.delay(str(source.id))
                results.append({"source_id": str(source.id), "task_id": res.id})
            except Exception as e:
                results.append({"source_id": str(source.id), "error": str(e)})
        return {"fetched": len(results), "results": results}

    return run_async(_run())
