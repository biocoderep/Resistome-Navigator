"""Batch and Cohort models."""

import uuid
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from backend.database.base import Base

# Note: Since SQLite doesn't support JSONB, we fallback to JSON
import sqlalchemy
from sqlalchemy.dialects.sqlite import JSON

class Batch(Base):
    __tablename__ = "batches"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, index=True, nullable=True)
    batch_name = Column(String, nullable=True)
    run_cohort_analysis = Column(Boolean, default=True)
    total_isolates = Column(Integer, default=0)
    completed_isolates = Column(Integer, default=0)
    failed_isolates = Column(Integer, default=0)
    status = Column(String, default="DISPATCHING")  # DISPATCHING, RUNNING, COMPLETED, PARTIAL_FAILED, FAILED
    cohort_analysis_status = Column(String, default="PENDING")  # PENDING, RUNNING, COMPLETED, FAILED

    samples = relationship("Sample", back_populates="batch")
    cohort_results = relationship("CohortResult", back_populates="batch")


class CohortResult(Base):
    __tablename__ = "cohort_results"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    batch_id = Column(String, ForeignKey("batches.id"), index=True)
    analysis_type = Column(String, index=True)  # e.g., "umap", "network", "barcode"
    
    # Use JSON for sqlite compatibility
    result_json = Column(JSON, nullable=True)

    batch = relationship("Batch", back_populates="cohort_results")
