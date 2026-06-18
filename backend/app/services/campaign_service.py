from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.campaign import Campaign, CampaignGmailAccount, CampaignLead
from app.models.gmail import GmailAccount
from app.models.sheet_source import SheetSource
from app.services.google_sheet_service import GoogleSheetService


class CampaignService:
    @staticmethod
    async def create_campaign(
        db: AsyncSession, user_id: UUID, data: dict
    ) -> Campaign:
        campaign = Campaign(
            user_id=user_id,
            name=data.get("name"),
            template_id=data.get("template_id"),
            sheet_source_id=data.get("sheet_source_id"),
            daily_limit=data.get("daily_limit", 50),
            sending_window_start=data.get("sending_window_start", "09:00"),
            sending_window_end=data.get("sending_window_end", "17:00"),
            status="draft",
        )
        db.add(campaign)
        await db.flush()
        gmail_account_ids = data.get("gmail_account_ids", [])
        for idx, account_id in enumerate(gmail_account_ids):
            cga = CampaignGmailAccount(
                campaign_id=campaign.id,
                gmail_account_id=account_id,
                order=idx,
            )
            db.add(cga)
        if data.get("sheet_source_id"):
            result = await db.execute(
                select(SheetSource).where(SheetSource.id == data["sheet_source_id"])
            )
            sheet_source = result.scalar_one_or_none()
            if sheet_source:
                await GoogleSheetService.fetch_pending_leads(db, sheet_source, user_id)
                from sqlalchemy import func as sqlfunc
                count_result = await db.execute(
                    select(sqlfunc.count())
                    .select_from(CampaignLead)
                    .where(CampaignLead.campaign_id == campaign.id)
                )
                campaign.lead_count = count_result.scalar()
        await db.commit()
        await db.refresh(campaign)
        return campaign

    @staticmethod
    async def get_campaigns(db: AsyncSession, user_id: UUID) -> list:
        result = await db.execute(
            select(Campaign)
            .where(Campaign.user_id == user_id)
            .order_by(Campaign.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_campaign(db: AsyncSession, campaign_id: UUID) -> Campaign:
        result = await db.execute(
            select(Campaign)
            .options(
                selectinload(Campaign.template),
                selectinload(Campaign.sheet_source),
                selectinload(Campaign.gmail_accounts).selectinload(CampaignGmailAccount.gmail_account),
                selectinload(Campaign.leads),
            )
            .where(Campaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()
        if not campaign:
            raise ValueError("Campaign not found")
        return campaign

    @staticmethod
    async def update_campaign(
        db: AsyncSession, campaign_id: UUID, data: dict
    ) -> Campaign:
        campaign = await CampaignService.get_campaign(db, campaign_id)
        for field, value in data.items():
            if hasattr(campaign, field):
                setattr(campaign, field, value)
        await db.commit()
        await db.refresh(campaign)
        return campaign

    @staticmethod
    async def delete_campaign(db: AsyncSession, campaign_id: UUID) -> bool:
        campaign = await CampaignService.get_campaign(db, campaign_id)
        await db.delete(campaign)
        await db.commit()
        return True

    @staticmethod
    async def start_campaign(
        db: AsyncSession, campaign_id: UUID
    ) -> Campaign:
        campaign = await CampaignService.get_campaign(db, campaign_id)
        if campaign.status != "draft" and campaign.status != "paused":
            raise ValueError(f"Cannot start campaign with status {campaign.status}")
        if not campaign.template_id:
            raise ValueError("Campaign has no template")
        if not campaign.gmail_accounts:
            raise ValueError("Campaign has no Gmail accounts")
        sheet_source = campaign.sheet_source
        if sheet_source:
            await GoogleSheetService.fetch_pending_leads(db, sheet_source, campaign.user_id)
        from sqlalchemy import func as sqlfunc
        from app.models.lead import Lead
        leads_result = await db.execute(
            select(Lead).where(
                Lead.sheet_source_id == sheet_source.id,
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
                campaign_lead = CampaignLead(
                    campaign_id=campaign.id,
                    lead_id=lead.id,
                    status="pending",
                )
                db.add(campaign_lead)
        campaign.status = "running"
        campaign.started_at = datetime.utcnow()
        campaign.last_processed_index = 0
        await db.commit()
        await db.refresh(campaign)
        return campaign

    @staticmethod
    async def pause_campaign(db: AsyncSession, campaign_id: UUID) -> Campaign:
        campaign = await CampaignService.get_campaign(db, campaign_id)
        if campaign.status != "running":
            raise ValueError("Campaign is not running")
        campaign.status = "paused"
        campaign.paused_at = datetime.utcnow()
        await db.commit()
        await db.refresh(campaign)
        return campaign

    @staticmethod
    async def resume_campaign(db: AsyncSession, campaign_id: UUID) -> Campaign:
        campaign = await CampaignService.get_campaign(db, campaign_id)
        if campaign.status != "paused":
            raise ValueError("Campaign is not paused")
        campaign.status = "running"
        campaign.resumed_at = datetime.utcnow()
        await db.commit()
        await db.refresh(campaign)
        return campaign

    @staticmethod
    async def get_campaign_stats(db: AsyncSession, campaign_id: UUID) -> dict:
        campaign = await CampaignService.get_campaign(db, campaign_id)
        leads = campaign.leads
        total = len(leads)
        sent = sum(1 for l in leads if l.status == "sent")
        failed = sum(1 for l in leads if l.status == "failed")
        pending = sum(1 for l in leads if l.status == "pending")
        replied = sum(1 for l in leads if l.replied_at is not None)
        return {
            "campaign_id": str(campaign_id),
            "name": campaign.name,
            "status": campaign.status,
            "total_leads": total,
            "sent": sent,
            "failed": failed,
            "pending": pending,
            "replied": replied,
            "reply_rate": round(replied / sent * 100, 2) if sent else 0,
            "progress": round(sent / total * 100, 2) if total else 0,
        }
