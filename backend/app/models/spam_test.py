import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class SpamTest(Base):
    __tablename__ = "spam_tests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    gmail_account_id = Column(UUID(as_uuid=True), ForeignKey("gmail_accounts.id", ondelete="SET NULL"), nullable=True)
    subject = Column(String(512), nullable=False)
    body = Column(Text, nullable=False)
    spam_score = Column(Float, default=0.0, nullable=False)
    deliverability_score = Column(Float, default=0.0, nullable=False)
    recommendations = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="spam_tests")
    gmail_account = relationship("GmailAccount", back_populates="spam_tests")
