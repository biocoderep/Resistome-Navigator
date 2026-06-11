"""ConfidenceScore ORM model."""

from __future__ import annotations

import decimal
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Numeric, String, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.models.analysis_job import AnalysisJob
    from backend.models.sample import Sample


class ConfidenceScore(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A confidence score for a detected entity (gene, mutation, phenotype, virulence)."""

    __tablename__ = "confidence_scores"

    sample_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("samples.id", ondelete="CASCADE"),
        nullable=False,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    context: Mapped[str] = mapped_column(String(50), nullable=False) # e.g., "amr_gene", "phenotype"
    target_name: Mapped[str] = mapped_column(String(200), nullable=False) # e.g., "blaTEM-1", "MEM"
    overall_score: Mapped[decimal.Decimal] = mapped_column(Numeric(6, 3), nullable=False)
    tier: Mapped[str] = mapped_column(String(50), nullable=False)
    cap_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    components: Mapped[dict] = mapped_column(JSON, default=dict)
    weighted: Mapped[dict] = mapped_column(JSON, default=dict)

    sample: Mapped["Sample"] = relationship()
    job: Mapped["AnalysisJob"] = relationship()

    __table_args__ = (
        Index("idx_confidence_scores_sample", "sample_id"),
        Index("idx_confidence_scores_job", "job_id"),
        Index("idx_confidence_scores_target", "target_name"),
    )


__all__ = ["ConfidenceScore"]
