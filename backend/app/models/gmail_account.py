import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class GmailAccount(Base):
    __tablename__ = "gmail_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    token_expiry = Column(DateTime(timezone=True), nullable=False)
    daily_limit = Column(Integer, default=500, nullable=False)
    hourly_limit = Column(Integer, default=50, nullable=False)
    daily_sent = Column(Integer, default=0, nullable=False)
    hourly_sent = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    health_score = Column(Float, default=100.0, nullable=False)
    inbox_rate = Column(Float, default=0.0, nullable=False)
    spam_rate = Column(Float, default=0.0, nullable=False)
    reply_rate = Column(Float, default=0.0, nullable=False)
    warmup_status = Column(String(20), default="none", nullable=False)
    warmup_progress = Column(Integer, default=0, nullable=False)
    last_sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="gmail_accounts")
    campaign_gmail_accounts = relationship("CampaignGmailAccount", back_populates="gmail_account", cascade="all, delete-orphan")
    campaign_leads = relationship("CampaignLead", back_populates="gmail_account")
    email_messages = relationship("EmailMessage", back_populates="gmail_account")
    email_replies = relationship("EmailReply", back_populates="gmail_account")
    spam_tests = relationship("SpamTest", back_populates="gmail_account")
    warmup_progress = relationship("WarmupProgress", back_populates="gmail_account", cascade="all, delete-orphan")
