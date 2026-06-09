"""Base classes for alignment operations."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AlignmentMethod(str, Enum):
    """Supported alignment methods."""

    BOWTIE2 = "bowtie2"
    BWA = "bwa"
    MINIMAP2 = "minimap2"


class AlignmentConfig(BaseModel):
    """Configuration for alignment operations."""

    method: AlignmentMethod = Field(default=AlignmentMethod.BOWTIE2)
    threads: int = Field(default=4, ge=1, le=128)
    max_mismatch_percent: float = Field(default=5.0, ge=0.0, le=100.0)
    min_alignment_length: int = Field(default=50, ge=20)
    min_match_identity: float = Field(default=95.0, ge=0.0, le=100.0)
    keep_unmapped: bool = Field(default=True)
    output_format: str = Field(default="bam")  # bam, sam, paf


class AlignmentHit(BaseModel):
    """Single alignment hit (mapping)."""

    query_name: str
    subject_name: str
    query_start: int
    query_end: int
    subject_start: int
    subject_end: int
    match_length: int
    identity_percent: float
    alignment_length: int
    e_value: Optional[float] = None
    bit_score: Optional[float] = None
    cigar: Optional[str] = None


class AlignmentResult(BaseModel):
    """Results from alignment operation."""

    alignment_id: UUID
    sample_id: UUID
    assembly_id: UUID
    reference_db: str
    method: AlignmentMethod
    total_queries: int
    mapped_queries: int
    mapped_percent: float
    unmapped_queries: int
    hits: list[AlignmentHit] = Field(default_factory=list)
    output_file: Optional[Path] = None
    stats: dict = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


class BaseAligner:
    """Base class for alignment tools."""

    def __init__(self, config: AlignmentConfig):
        """Initialize aligner with config."""
        self.config = config

    def align(
        self,
        query_file: Path,
        reference_db: Path,
        output_file: Path,
        progress_callback=None,
    ) -> AlignmentResult:
        """
        Execute alignment.

        Args:
            query_file: Path to query FASTA file
            reference_db: Path to reference database
            output_file: Path for output file
            progress_callback: Optional callback for progress updates

        Returns:
            AlignmentResult with mapping statistics
        """
        raise NotImplementedError("Subclasses must implement align()")

    def parse_output(self, output_file: Path) -> list[AlignmentHit]:
        """
        Parse alignment output file.

        Args:
            output_file: Path to output file

        Returns:
            List of AlignmentHit objects
        """
        raise NotImplementedError("Subclasses must implement parse_output()")
