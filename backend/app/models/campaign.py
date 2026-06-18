import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    sheet_source_id = Column(UUID(as_uuid=True), ForeignKey("sheet_sources.id", ondelete="SET NULL"), nullable=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("templates.id", ondelete="SET NULL"), nullable=True)
    daily_limit = Column(Integer, default=50, nullable=False)
    sending_window_start = Column(String(5), default="09:00", nullable=False)
    sending_window_end = Column(String(5), default="17:00", nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)
    min_delay = Column(Integer, default=40, nullable=False)
    max_delay = Column(Integer, default=60, nullable=False)
    status = Column(String(20), default="draft", nullable=False)
    total_leads = Column(Integer, default=0, nullable=False)
    sent_count = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)
    reply_count = Column(Integer, default=0, nullable=False)
    open_count = Column(Integer, default=0, nullable=False)
    bounce_count = Column(Integer, default=0, nullable=False)
    last_processed_index = Column(Integer, default=0, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="campaigns")
    sheet_source = relationship("SheetSource", back_populates="campaigns")
    campaign_gmail_accounts = relationship("CampaignGmailAccount", back_populates="campaign", cascade="all, delete-orphan")
    campaign_leads = relationship("CampaignLead", back_populates="campaign", cascade="all, delete-orphan")
    email_messages = relationship("EmailMessage", back_populates="campaign")


class CampaignGmailAccount(Base):
    __tablename__ = "campaign_gmail_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    gmail_account_id = Column(UUID(as_uuid=True), ForeignKey("gmail_accounts.id", ondelete="CASCADE"), nullable=False)

    campaign = relationship("Campaign", back_populates="campaign_gmail_accounts")
    gmail_account = relationship("GmailAccount", back_populates="campaign_gmail_accounts")


class CampaignLead(Base):
    __tablename__ = "campaign_leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    replied_at = Column(DateTime(timezone=True), nullable=True)
    gmail_account_id = Column(UUID(as_uuid=True), ForeignKey("gmail_accounts.id", ondelete="SET NULL"), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)

    campaign = relationship("Campaign", back_populates="campaign_leads")
    lead = relationship("Lead", back_populates="campaign_leads")
    gmail_account = relationship("GmailAccount", back_populates="campaign_leads")
