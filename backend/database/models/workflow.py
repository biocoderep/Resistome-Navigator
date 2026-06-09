"""Workflow execution models."""

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship
from sqlalchemy import Uuid
from .base import Base, generate_uuid, utcnow

class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=generate_uuid)
    sample_id = Column(Uuid(as_uuid=True), ForeignKey("samples.id", ondelete="SET NULL"))
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    submitted_by = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    celery_task_id = Column(String(255))
    status = Column(String(30), nullable=False, default="QUEUED")
    priority = Column(Integer, nullable=False, default=5)
    queue_name = Column(String(50), default="default")
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    error_code = Column(String(100))
    error_message = Column(String)
    
    submitted_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    analysis_config = Column(JSON)
    
    sample = relationship("Sample")
    project = relationship("Project")
    user = relationship("User")
