"""PhenotypePrediction ORM model."""

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


class PhenotypePrediction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A predicted phenotype (S/I/R) for a sample."""

    __tablename__ = "phenotype_predictions"

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
    drug: Mapped[str] = mapped_column(String(200), nullable=False)
    drug_class: Mapped[str | None] = mapped_column(String(200), nullable=True)
    predicted_sir: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence_score: Mapped[decimal.Decimal | None] = mapped_column(
        Numeric(6, 3), nullable=True
    )
    confidence_tier: Mapped[str | None] = mapped_column(String(50), nullable=True)
    breakpoint_source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    breakpoint_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_not_testable: Mapped[bool] = mapped_column(Boolean, default=False)
    has_conflict: Mapped[bool] = mapped_column(Boolean, default=False)
    supporting_genes: Mapped[list[str]] = mapped_column(JSON, default=list)
    supporting_mutations: Mapped[list[str]] = mapped_column(JSON, default=list)
    explanation: Mapped[str | None] = mapped_column(String, nullable=True)

    sample: Mapped["Sample"] = relationship()
    job: Mapped["AnalysisJob"] = relationship()

    __table_args__ = (
        Index("idx_phenotype_preds_sample", "sample_id"),
        Index("idx_phenotype_preds_job", "job_id"),
        Index("idx_phenotype_preds_drug", "drug"),
    )


__all__ = ["PhenotypePrediction"]
