"""AmrHit ORM model."""

from __future__ import annotations

import decimal
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.models.amr_gene import AmrGene


class AmrHit(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A per-tool alignment hit supporting an AMR gene call."""

    __tablename__ = "amr_hits"

    amr_gene_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("amr_genes.id", ondelete="CASCADE"),
        nullable=False,
    )
    tool_name: Mapped[str] = mapped_column(String(50), nullable=False)
    identity: Mapped[decimal.Decimal | None] = mapped_column(Numeric(6, 3), nullable=True)
    coverage: Mapped[decimal.Decimal | None] = mapped_column(Numeric(6, 3), nullable=True)
    bit_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    evalue: Mapped[float | None] = mapped_column(Float, nullable=True)
    prediction: Mapped[str | None] = mapped_column(String(100), nullable=True)

    amr_gene: Mapped["AmrGene"] = relationship(back_populates="hits")

    __table_args__ = (Index("idx_amr_hits_gene", "amr_gene_id"),)


__all__ = ["AmrHit"]