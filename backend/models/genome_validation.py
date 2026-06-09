"""Database models for genome validation."""

from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, JSON, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.models.sample import Sample


class Assembly(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """An assembly (typically uploaded FASTA file) for a sample."""

    __tablename__ = "assemblies"

    sample_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("samples.id", ondelete="CASCADE"),
        nullable=False,
    )
    assembler: Mapped[str | None] = mapped_column(String(100), nullable=True)
    assembly_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="UPLOADED", server_default="UPLOADED"
    )

    sample: Mapped["Sample"] = relationship(back_populates="assemblies")
    metrics: Mapped["AssemblyMetrics"] = relationship(
        back_populates="assembly",
        cascade="all, delete-orphan",
        uselist=False,
    )
    validation_reports: Mapped[list["ValidationReport"]] = relationship(
        back_populates="assembly",
        cascade="all, delete-orphan",
    )

    __table_args__ = (Index("idx_assemblies_sample", "sample_id"),)


class AssemblyMetrics(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Assembly statistics for a validated genome."""

    __tablename__ = "assembly_metrics"

    assembly_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assemblies.id", ondelete="CASCADE"),
        nullable=False,
    )
    total_length_bp: Mapped[int] = mapped_column(nullable=False)
    contig_count: Mapped[int] = mapped_column(nullable=False)
    mean_contig_bp: Mapped[float] = mapped_column(nullable=False)
    median_contig_bp: Mapped[float] = mapped_column(nullable=False)
    max_contig_bp: Mapped[int] = mapped_column(nullable=False)
    min_contig_bp: Mapped[int] = mapped_column(nullable=False)
    n50_bp: Mapped[int] = mapped_column(nullable=False)
    n90_bp: Mapped[int] = mapped_column(nullable=False)
    l50: Mapped[int] = mapped_column(nullable=False)
    gc_percent: Mapped[float] = mapped_column(nullable=False)
    n_percent: Mapped[float] = mapped_column(nullable=False)
    assembly_span_bp: Mapped[int] = mapped_column(nullable=False)
    
    # Extended quality metrics
    quality_score: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    quality_classification: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    confidence_cap: Mapped[str] = mapped_column(
        String(20), nullable=False, default="FULL", server_default="FULL"
    )
    contamination_risk: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    contamination_signals: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    gc_outlier_contigs: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    gc_variance: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    gc_std_dev: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    duplicate_pairs: Mapped[int] = mapped_column(default=0, server_default="0")
    mean_shannon_entropy: Mapped[float | None] = mapped_column(
        Numeric(6, 4), nullable=True
    )
    kmer_coverage_estimate: Mapped[float | None] = mapped_column(
        Numeric(8, 2), nullable=True
    )
    taxonomy_status: Mapped[str | None] = mapped_column(String(30), nullable=True)

    assembly: Mapped["Assembly"] = relationship(back_populates="metrics")

    __table_args__ = (Index("idx_assembly_metrics_assembly", "assembly_id"),)


class ValidationReport(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Validation report for an assembly (one per validation run)."""

    __tablename__ = "validation_reports"

    assembly_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assemblies.id", ondelete="CASCADE"),
        nullable=False,
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    validation_status: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # PASS, WARNING, FAIL
    quality_score: Mapped[float] = mapped_column(nullable=False)
    quality_class: Mapped[str] = mapped_column(String(20), nullable=False)
    proceed_to_amr: Mapped[bool] = mapped_column(nullable=False)
    confidence_cap: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Full report JSON
    full_report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Errors and warnings
    errors: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    warnings: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Override tracking
    override_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    override_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    override_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    assembly: Mapped["Assembly"] = relationship(back_populates="validation_reports")

    __table_args__ = (Index("idx_validation_reports_assembly", "assembly_id"),)
