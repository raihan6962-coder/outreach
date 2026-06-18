import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class PipelineStage(Base):
    __tablename__ = "pipeline_stages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    position = Column(Integer, nullable=False)
    color = Column(String(20), default="#6366f1", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="pipeline_stages")
    lead_pipelines = relationship("LeadPipeline", back_populates="stage", cascade="all, delete-orphan")


class LeadPipeline(Base):
    __tablename__ = "lead_pipelines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    stage_id = Column(UUID(as_uuid=True), ForeignKey("pipeline_stages.id", ondelete="CASCADE"), nullable=False)
    moved_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    lead = relationship("Lead", back_populates="lead_pipelines")
    stage = relationship("PipelineStage", back_populates="lead_pipelines")
