"""Pydantic v2 schemas for analysis jobs and AMR results."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AnalysisRunRequest(BaseModel):
    """Payload to submit an analysis job for a sample."""

    model_config = ConfigDict(str_strip_whitespace=True)

    sample_id: UUID
    job_type: str = Field(default="amr_detection", min_length=1, max_length=50)


class AnalysisJobResponse(BaseModel):
    """An analysis job record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sample_id: UUID
    job_type: str
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class AmrHitResponse(BaseModel):
    """A per-tool alignment hit supporting a gene call."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    amr_gene_id: UUID
    tool_name: str
    identity: Decimal | None = None
    coverage: Decimal | None = None
    bit_score: float | None = None
    evalue: float | None = None
    prediction: str | None = None
    created_at: datetime
    updated_at: datetime


class AmrGeneResponse(BaseModel):
    """A detected AMR gene with its supporting hits."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sample_id: UUID
    job_id: UUID
    gene_name: str
    gene_family: str | None = None
    antibiotic_class: str | None = None
    resistance_mechanism: str | None = None
    confidence_score: Decimal | None = None
    created_at: datetime
    updated_at: datetime
    hits: list[AmrHitResponse] = Field(default_factory=list)


class AnalysisJobDetailResponse(AnalysisJobResponse):
    """Analysis job with its detected AMR genes."""

    amr_genes: list[AmrGeneResponse] = Field(default_factory=list)