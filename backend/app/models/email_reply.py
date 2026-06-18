import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class EmailReply(Base):
    __tablename__ = "email_replies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email_message_id = Column(UUID(as_uuid=True), ForeignKey("email_messages.id", ondelete="CASCADE"), nullable=False)
    gmail_account_id = Column(UUID(as_uuid=True), ForeignKey("gmail_accounts.id", ondelete="CASCADE"), nullable=False)
    from_email = Column(String(255), nullable=False)
    subject = Column(String(512), nullable=False)
    body_snippet = Column(Text, nullable=True)
    reply_type = Column(String(20), default="reply", nullable=False)
    is_positive = Column(Boolean, nullable=True)
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    email_message = relationship("EmailMessage", back_populates="email_replies")
    gmail_account = relationship("GmailAccount", back_populates="email_replies")
