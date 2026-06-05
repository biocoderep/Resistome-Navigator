"""AmrGene ORM model."""

from __future__ import annotations

import decimal
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.models.amr_hit import AmrHit
    from backend.models.analysis_job import AnalysisJob
    from backend.models.sample import Sample


class AmrGene(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A detected antimicrobial-resistance gene call for a sample."""

    __tablename__ = "amr_genes"

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
    gene_family: Mapped[str | None] = mapped_column(String(200), nullable=True)
    antibiotic_class: Mapped[str | None] = mapped_column(String(200), nullable=True)
    resistance_mechanism: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confidence_score: Mapped[decimal.Decimal | None] = mapped_column(
        Numeric(5, 4), nullable=True
    )

    sample: Mapped["Sample"] = relationship(back_populates="amr_genes")
    job: Mapped["AnalysisJob"] = relationship(back_populates="amr_genes")
    hits: Mapped[list["AmrHit"]] = relationship(
        back_populates="amr_gene",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("idx_amr_genes_sample", "sample_id"),
        Index("idx_amr_genes_job", "job_id"),
        Index("idx_amr_genes_gene_name", "gene_name"),
    )


__all__ = ["AmrGene"]