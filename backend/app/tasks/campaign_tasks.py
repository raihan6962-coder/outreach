import asyncio
import random
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from celery import current_task

from app.tasks.celery_app import celery_app
from app.database import async_session_maker
from app.models.campaign import Campaign, CampaignLead
from app.models.gmail_account import GmailAccount
from app.models.lead import Lead
from app.models.email_message import EmailMessage
from app.services.sending_engine import SendingEngine
from app.services.email_validation_service import EmailValidationService
from app.services.rotation_service import RotationService
from app.services.personalization_service import PersonalizationService
from app.services.template_service import TemplateService
from app.utils.gmail_client import GmailClient


def run_async(coro):
    return asyncio.run(coro)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_campaign(self, campaign_id: str):
    async def _run():
        async with async_session_maker() as db:
            result = await db.execute(
                select(Campaign)
                .options(
                    selectinload(Campaign.campaign_leads).selectinload(CampaignLead.lead),
                    selectinload(Campaign.campaign_gmail_accounts).selectinload(CampaignGmailAccount.gmail_account),
                    selectinload(Campaign.template),
                )
                .where(Campaign.id == UUID(campaign_id))
            )
            campaign = result.scalar_one_or_none()
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")

            if campaign.status != "running":
                return {"campaign_id": campaign_id, "status": "not_running"}

            now = datetime.now(timezone.utc)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

            sent_today_result = await db.execute(
                select(CampaignLead)
                .where(
                    CampaignLead.campaign_id == campaign.id,
                    CampaignLead.status == "sent",
                    CampaignLead.sent_at >= today_start,
                )
            )
            sent_today = len(list(sent_today_result.scalars().all()))
            remaining = campaign.daily_limit - sent_today

            if remaining <= 0:
                return {"campaign_id": campaign_id, "status": "daily_limit_reached", "sent_today": sent_today}

            pending_result = await db.execute(
                select(CampaignLead)
                .options(selectinload(CampaignLead.lead))
                .where(
                    CampaignLead.campaign_id == campaign.id,
                    CampaignLead.status == "pending",
                )
                .order_by(CampaignLead.created_at.asc())
                .limit(remaining)
            )
            pending_leads = list(pending_result.scalars().all())

            if not pending_leads:
                campaign.status = "completed"
                campaign.completed_at = now
                await db.commit()
                return {"campaign_id": campaign_id, "status": "completed"}

            sent = 0
            failed = 0

            for campaign_lead in pending_leads:
                if current_task and current_task.request.canceled:
                    break

                campaign_check = await db.execute(
                    select(Campaign).where(Campaign.id == UUID(campaign_id))
                )
                c = campaign_check.scalar_one_or_none()
                if not c or c.status != "running":
                    break

                try:
                    validation = await EmailValidationService.validate_lead_email(db, campaign_lead.lead)
                    if not validation.get("is_valid"):
                        campaign_lead.status = "failed"
                        campaign_lead.error_message = "Email validation failed"
                        await db.commit()
                        failed += 1
                        continue

                    result_data = await SendingEngine.send_email(db, campaign_lead.id)
                    if result_data.get("success"):
                        sent += 1
                    else:
                        campaign_lead.status = "failed"
                        campaign_lead.error_message = result_data.get("error", "Send failed")
                        await db.commit()
                        failed += 1
                except Exception as e:
                    campaign_lead.status = "failed"
                    campaign_lead.error_message = str(e)
                    await db.commit()
                    failed += 1

                await asyncio.sleep(random.uniform(campaign.min_delay, campaign.max_delay))

            remaining_check = await db.execute(
                select(CampaignLead)
                .where(
                    CampaignLead.campaign_id == campaign.id,
                    CampaignLead.status == "pending",
                )
            )
            still_pending = remaining_check.scalar_one_or_none()

            if not still_pending:
                campaign.status = "completed"
                campaign.completed_at = datetime.now(timezone.utc)
                await db.commit()

            return {
                "campaign_id": campaign_id,
                "sent": sent,
                "failed": failed,
                "status": campaign.status,
            }

    try:
        return run_async(_run())
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True)
def start_campaign(self, campaign_id: str):
    async def _run():
        async with async_session_maker() as db:
            result = await db.execute(
                select(Campaign)
                .options(
                    selectinload(Campaign.sheet_source),
                    selectinload(Campaign.campaign_gmail_accounts),
                )
                .where(Campaign.id == UUID(campaign_id))
            )
            campaign = result.scalar_one_or_none()
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")

            if campaign.status not in ("draft", "paused"):
                return {"campaign_id": campaign_id, "status": f"cannot_start_from_{campaign.status}"}

            if campaign.sheet_source:
                from app.services.google_sheet_service import GoogleSheetService
                await GoogleSheetService.fetch_pending_leads(db, campaign.sheet_source, campaign.user_id)

                leads_result = await db.execute(
                    select(Lead).where(
                        Lead.sheet_source_id == campaign.sheet_source.id,
                        Lead.user_id == campaign.user_id,
                    )
                )
                leads = list(leads_result.scalars().all())

                for lead in leads:
                    existing = await db.execute(
                        select(CampaignLead).where(
                            CampaignLead.campaign_id == campaign.id,
                            CampaignLead.lead_id == lead.id,
                        )
                    )
                    if not existing.scalar_one_or_none():
                        cl = CampaignLead(
                            campaign_id=campaign.id,
                            lead_id=lead.id,
                            status="pending",
                        )
                        db.add(cl)

            campaign.status = "running"
            campaign.started_at = datetime.now(timezone.utc)
            campaign.last_processed_index = 0
            await db.commit()

    run_async(_run())
    process_campaign.delay(campaign_id)
    return {"campaign_id": campaign_id, "status": "started"}


@celery_app.task
def pause_campaign(campaign_id: str):
    async def _run():
        async with async_session_maker() as db:
            result = await db.execute(
                select(Campaign).where(Campaign.id == UUID(campaign_id))
            )
            campaign = result.scalar_one_or_none()
            if campaign and campaign.status == "running":
                campaign.status = "paused"
                await db.commit()

    run_async(_run())
    celery_app.control.revoke(
        celery_app.control.inspect().scheduled().get(campaign_id, []),
        terminate=True,
    )
    return {"campaign_id": campaign_id, "status": "paused"}


@celery_app.task
def reset_daily_counts():
    async def _run():
        async with async_session_maker() as db:
            now = datetime.now(timezone.utc)
            await db.execute(
                update(GmailAccount).values(
                    daily_sent=0,
                    hourly_sent=0,
                )
            )
            await db.commit()

    run_async(_run())
    return {"status": "daily_counts_reset"}
