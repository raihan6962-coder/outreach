import uuid
from datetime import date as date_type
from sqlalchemy import Column, Integer, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class WarmupProgress(Base):
    __tablename__ = "warmup_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gmail_account_id = Column(UUID(as_uuid=True), ForeignKey("gmail_accounts.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    target_count = Column(Integer, default=0, nullable=False)
    sent_count = Column(Integer, default=0, nullable=False)
    inbox_count = Column(Integer, default=0, nullable=False)
    spam_count = Column(Integer, default=0, nullable=False)
    reply_count = Column(Integer, default=0, nullable=False)

    gmail_account = relationship("GmailAccount", back_populates="warmup_progress")
