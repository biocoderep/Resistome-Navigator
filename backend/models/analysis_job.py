"""AnalysisJob ORM model."""

from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.models.amr_gene import AmrGene
    from backend.models.sample import Sample


class AnalysisJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """An analysis run executed against a sample."""

    __tablename__ = "analysis_jobs"

    sample_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("samples.id", ondelete="CASCADE"),
        nullable=False,
    )
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="QUEUED", server_default="QUEUED"
    )
    started_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    sample: Mapped["Sample"] = relationship(back_populates="analysis_jobs")
    amr_genes: Mapped[list["AmrGene"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("idx_analysis_jobs_sample", "sample_id"),
        Index("idx_analysis_jobs_status", "status"),
    )


__all__ = ["AnalysisJob"]