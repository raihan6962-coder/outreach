import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    sheet_source_id = Column(UUID(as_uuid=True), ForeignKey("sheet_sources.id", ondelete="SET NULL"), nullable=True)
    app_id = Column(String(255), nullable=True)
    app_name = Column(String(255), nullable=True)
    developer = Column(String(255), nullable=True)
    email = Column(String(255), nullable=False, index=True)
    category = Column(String(255), nullable=True)
    installs = Column(Integer, nullable=True)
    score = Column(Float, nullable=True)
    url = Column(String(512), nullable=True)
    keyword = Column(String(255), nullable=True)
    validation_status = Column(String(20), default="pending", nullable=False)
    is_sent = Column(Boolean, default=False, nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    tags = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    history = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="leads")
    sheet_source = relationship("SheetSource", back_populates="leads")
    email_validation = relationship("EmailValidation", back_populates="lead", uselist=False, cascade="all, delete-orphan")
    campaign_leads = relationship("CampaignLead", back_populates="lead", cascade="all, delete-orphan")
    lead_pipelines = relationship("LeadPipeline", back_populates="lead", cascade="all, delete-orphan")
