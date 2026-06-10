"""Sample ORM model."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, Index, Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.models.amr_gene import AmrGene
    from backend.models.analysis_job import AnalysisJob
    from backend.models.genome_validation import Assembly
    from backend.models.sample_file import SampleFile


class Sample(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A genomic isolate submitted for AMR characterisation."""

    __tablename__ = "samples"

    isolate_name: Mapped[str] = mapped_column(String(200), nullable=False)
    species: Mapped[str | None] = mapped_column(String(200), nullable=True)
    species_taxid: Mapped[int | None] = mapped_column(Integer, nullable=True)
    host: Mapped[str | None] = mapped_column(String(100), nullable=True)
    collection_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    source_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(3), nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="UPLOADED", server_default="UPLOADED"
    )
    batch_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("batches.id"), nullable=True)
    project_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    batch = relationship("Batch", back_populates="samples")
    files: Mapped[list["SampleFile"]] = relationship(
        back_populates="sample",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    assemblies: Mapped[list["Assembly"]] = relationship(
        back_populates="sample",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    analysis_jobs: Mapped[list["AnalysisJob"]] = relationship(
        back_populates="sample",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    amr_genes: Mapped[list["AmrGene"]] = relationship(
        back_populates="sample",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("idx_samples_species", "species"),
        Index("idx_samples_status", "status"),
    )


__all__ = ["Sample"]