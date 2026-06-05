"""Pydantic v2 schemas for samples and sample files."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

SourceType = Literal["clinical", "environmental", "surveillance"]


class SampleCreateRequest(BaseModel):
    """Payload for registering a new sample."""

    model_config = ConfigDict(str_strip_whitespace=True)

    isolate_name: str = Field(min_length=1, max_length=200)
    species: str | None = Field(default=None, max_length=200)
    species_taxid: int | None = Field(default=None, gt=0)
    host: str | None = Field(default=None, max_length=100)
    collection_date: date | None = None
    source_type: SourceType | None = None
    location: str | None = Field(default=None, max_length=200)
    country_code: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")

    @field_validator("isolate_name")
    @classmethod
    def sanitise_name(cls, v: str) -> str:
        return v.strip()


class SampleFileResponse(BaseModel):
    """A file attached to a sample."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sample_id: UUID
    file_name: str
    file_path: str
    file_type: str
    file_size: int | None = None
    checksum: str | None = None
    created_at: datetime
    updated_at: datetime


class SampleResponse(BaseModel):
    """A registered sample."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    isolate_name: str
    species: str | None = None
    species_taxid: int | None = None
    host: str | None = None
    collection_date: date | None = None
    source_type: str | None = None
    location: str | None = None
    country_code: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime


class SampleDetailResponse(SampleResponse):
    """Sample with its associated files."""

    files: list[SampleFileResponse] = Field(default_factory=list)


class SampleListResponse(BaseModel):
    """Paginated list of samples."""

    items: list[SampleResponse]
    total: int
    page: int
    page_size: int