import asyncio
import random
from datetime import datetime, time
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.campaign import Campaign, CampaignLead, CampaignGmailAccount
from app.models.gmail import GmailAccount
from app.models.template import Template
from app.models.lead import Lead
from app.services.personalization_service import PersonalizationService
from app.services.template_service import TemplateService
from app.services.rotation_service import RotationService
from app.utils.gmail_client import GmailClient


class SendingEngine:
    @staticmethod
    async def send_email(db: AsyncSession, campaign_lead_id: UUID) -> dict:
        result = await db.execute(
            select(CampaignLead)
            .options(
                selectinload(CampaignLead.lead),
                selectinload(CampaignLead.campaign).selectinload(Campaign.template),
            )
            .where(CampaignLead.id == campaign_lead_id)
        )
        campaign_lead = result.scalar_one_or_none()
        if not campaign_lead:
            raise ValueError("CampaignLead not found")
        if campaign_lead.status == "sent":
            return {"success": True, "message": "Already sent"}

        campaign = campaign_lead.campaign
        lead = campaign_lead.lead
        template = campaign.template

        if not template:
            raise ValueError("Campaign has no template")

        gmail_account = await RotationService.get_optimal_account(db, campaign.id)
        if not gmail_account:
            raise ValueError("No available Gmail account with capacity")

        client = GmailClient(gmail_account)
        personalization = PersonalizationService.prepare_variables(lead)
        rendered = TemplateService.render_template(template, personalization)

        try:
            message_id = client.send_email(
                to=lead.email,
                subject=rendered["subject"],
                body_html=rendered["body_html"],
                body_text=rendered["body_text"],
            )
            campaign_lead.status = "sent"
            campaign_lead.sent_at = datetime.utcnow()
            campaign_lead.gmail_account_id = gmail_account.id
            campaign_lead.message_id = message_id
            await RotationService.update_account_usage(db, gmail_account.id)
            await db.commit()
            return {
                "success": True,
                "message_id": message_id,
                "account_email": gmail_account.email,
            }
        except Exception as e:
            campaign_lead.status = "failed"
            campaign_lead.error_message = str(e)
            await db.commit()
            return {"success": False, "error": str(e)}

    @staticmethod
    async def get_next_gmail(db: AsyncSession, campaign_id: UUID) -> GmailAccount:
        return await RotationService.get_optimal_account(db, campaign_id)

    @staticmethod
    async def process_campaign_batch(
        db: AsyncSession, campaign_id: UUID
    ) -> int:
        result = await db.execute(
            select(Campaign)
            .options(selectinload(Campaign.leads))
            .where(Campaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()
        if not campaign:
            raise ValueError("Campaign not found")
        if not await SendingEngine.should_send(db, campaign):
            return 0

        today_sent = sum(
            1 for l in campaign.leads if l.status == "sent"
        )
        remaining = campaign.daily_limit - today_sent
        if remaining <= 0:
            return 0

        pending_leads = [
            l for l in campaign.leads
            if l.status == "pending"
        ][:remaining]

        sent_count = 0
        for campaign_lead in pending_leads:
            if not await SendingEngine.should_send(db, campaign):
                break
            result = await SendingEngine.send_email(db, campaign_lead.id)
            if result.get("success"):
                sent_count += 1
            delay = random.uniform(40, 60)
            await asyncio.sleep(delay)

        return sent_count

    @staticmethod
    async def retry_failed(
        db: AsyncSession, campaign_lead_id: UUID
    ) -> bool:
        result = await db.execute(
            select(CampaignLead)
            .options(
                selectinload(CampaignLead.campaign)
                .selectinload(Campaign.gmail_accounts)
                .selectinload(CampaignGmailAccount.gmail_account)
            )
            .where(CampaignLead.id == campaign_lead_id)
        )
        campaign_lead = result.scalar_one_or_none()
        if not campaign_lead or campaign_lead.status != "failed":
            return False

        campaign = campaign_lead.campaign
        used_account_id = campaign_lead.gmail_account_id

        available_accounts = [
            cga.gmail_account
            for cga in campaign.gmail_accounts
            if cga.gmail_account.is_active
            and cga.gmail_account_id != used_account_id
            and cga.gmail_account.daily_sent < cga.gmail_account.daily_limit
        ]

        if not available_accounts:
            return False

        new_account = available_accounts[0]
        campaign_lead.gmail_account_id = new_account.id
        campaign_lead.status = "pending"
        campaign_lead.error_message = None
        await db.commit()

        send_result = await SendingEngine.send_email(db, campaign_lead.id)
        return send_result.get("success", False)

    @staticmethod
    async def should_send(db: AsyncSession, campaign) -> bool:
        if campaign.status != "running":
            return False

        now = datetime.utcnow().time()
        try:
            start = time.fromisoformat(campaign.sending_window_start)
            end = time.fromisoformat(campaign.sending_window_end)
        except (ValueError, TypeError):
            start = time(9, 0)
            end = time(17, 0)

        if start <= end:
            if now < start or now > end:
                return False
        else:
            if now < start and now > end:
                return False

        result = await db.execute(
            select(CampaignLead)
            .where(
                CampaignLead.campaign_id == campaign.id,
                CampaignLead.status == "sent",
                CampaignLead.sent_at
                >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
            )
        )
        today_sent = len(list(result.scalars().all()))
        if today_sent >= campaign.daily_limit:
            return False

        pending = await db.execute(
            select(CampaignLead).where(
                CampaignLead.campaign_id == campaign.id,
                CampaignLead.status == "pending",
            )
        )
        if not pending.scalar_one_or_none():
            return False

        return True
