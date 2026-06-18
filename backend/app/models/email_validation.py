import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class EmailValidation(Base):
    __tablename__ = "email_validations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), unique=True, nullable=False)
    syntax_valid = Column(Boolean, default=False, nullable=False)
    domain_valid = Column(Boolean, default=False, nullable=False)
    mx_valid = Column(Boolean, default=False, nullable=False)
    disposable = Column(Boolean, default=False, nullable=False)
    catch_all = Column(Boolean, default=False, nullable=False)
    smtp_valid = Column(Boolean, nullable=True)
    overall_valid = Column(Boolean, default=False, nullable=False)
    checked_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    lead = relationship("Lead", back_populates="email_validation")
