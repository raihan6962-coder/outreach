import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class EmailMessage(Base):
    __tablename__ = "email_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True)
    campaign_lead_id = Column(UUID(as_uuid=True), ForeignKey("campaign_leads.id", ondelete="SET NULL"), nullable=True)
    gmail_account_id = Column(UUID(as_uuid=True), ForeignKey("gmail_accounts.id", ondelete="CASCADE"), nullable=False)
    from_email = Column(String(255), nullable=False)
    to_email = Column(String(255), nullable=False)
    subject = Column(String(512), nullable=False)
    body = Column(Text, nullable=True)
    message_id = Column(String(255), nullable=True)
    thread_id = Column(String(255), nullable=True)
    status = Column(String(20), default="pending", nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    campaign = relationship("Campaign", back_populates="email_messages")
    gmail_account = relationship("GmailAccount", back_populates="email_messages")
    email_replies = relationship("EmailReply", back_populates="email_message", cascade="all, delete-orphan")
