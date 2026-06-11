"""VirulenceGene ORM model."""

from __future__ import annotations

import decimal
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.models.analysis_job import AnalysisJob
    from backend.models.sample import Sample


class VirulenceGene(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A detected virulence factor/gene for a sample."""

    __tablename__ = "virulence_genes"

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
    gene_name: Mapped[str] = mapped_column(String(200), nullable=False)
    virulence_factor: Mapped[str | None] = mapped_column(String(200), nullable=True)
    mechanism: Mapped[str | None] = mapped_column(String(200), nullable=True)
    contig_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    start_position: Mapped[int | None] = mapped_column(nullable=True)
    end_position: Mapped[int | None] = mapped_column(nullable=True)
    identity_percent: Mapped[decimal.Decimal | None] = mapped_column(
        Numeric(6, 3), nullable=True
    )
    coverage_percent: Mapped[decimal.Decimal | None] = mapped_column(
        Numeric(6, 3), nullable=True
    )
    database_source: Mapped[str | None] = mapped_column(String(100), nullable=True)

    sample: Mapped["Sample"] = relationship()
    job: Mapped["AnalysisJob"] = relationship()

    __table_args__ = (
        Index("idx_virulence_genes_sample", "sample_id"),
        Index("idx_virulence_genes_job", "job_id"),
        Index("idx_virulence_genes_name", "gene_name"),
    )


__all__ = ["VirulenceGene"]
