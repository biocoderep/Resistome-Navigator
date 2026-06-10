"""Batch and Cohort Analysis models."""

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship
from sqlalchemy import Uuid
from .base import Base, generate_uuid, utcnow

class Batch(Base):
    __tablename__ = "batches"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=generate_uuid)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    batch_name = Column(String(255))
    status = Column(String(50), nullable=False, default="QUEUED", index=True)
    total_isolates = Column(Integer, nullable=False)
    completed_isolates = Column(Integer, default=0)
    failed_isolates = Column(Integer, default=0)
    run_cohort_analysis = Column(Boolean, default=True)
    cohort_analysis_status = Column(String(50), default="PENDING")
    created_at = Column(DateTime(timezone=True), default=utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))

    # Relationships
    project = relationship("Project")
    creator = relationship("User")
    samples = relationship("Sample", back_populates="batch")
    cohort_results = relationship("CohortResult", back_populates="batch", cascade="all, delete-orphan")


class CohortResult(Base):
    __tablename__ = "cohort_results"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=generate_uuid)
    batch_id = Column(Uuid(as_uuid=True), ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_type = Column(String(100), nullable=False, index=True)
    result_json = Column(JSON, nullable=False)
    computed_at = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    batch = relationship("Batch", back_populates="cohort_results")
