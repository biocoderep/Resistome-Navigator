"""Base classes for AMR detection."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ResistanceClass(str, Enum):
    """Antibiotic resistance classes."""

    AMINOGLYCOSIDES = "Aminoglycosides"
    BETA_LACTAMS = "Beta-lactams"
    FLUOROQUINOLONES = "Fluoroquinolones"
    GLYCYLCYCLINES = "Glycylcyclines"
    MACROLIDES = "Macrolides"
    PHENICOLS = "Phenicols"
    RIFAMYCINS = "Rifamycins"
    TETRACYCLINES = "Tetracyclines"
    LIPOPEPTIDES = "Lipopeptides"
    OXAZOLIDINONES = "Oxazolidinones"
    FOSFOMYCIN = "Fosfomycin"
    SULFONAMIDES = "Sulfonamides"
    TRIMETHOPRIM = "Trimethoprim"
    POLYMYXINS = "Polymyxins"
    GLYCOPEPTIDES = "Glycopeptides"
    MULTI_DRUG = "Multi-drug"
    OTHER = "Other"


def map_resistance_class(raw: str) -> ResistanceClass:
    if not raw:
        return ResistanceClass.OTHER
    s = raw.lower()
    keywords = [
        ("aminoglycoside", ResistanceClass.AMINOGLYCOSIDES),
        ("beta-lactam", ResistanceClass.BETA_LACTAMS),
        ("cephalosporin", ResistanceClass.BETA_LACTAMS),
        ("cephamycin", ResistanceClass.BETA_LACTAMS),
        ("penam", ResistanceClass.BETA_LACTAMS),
        ("penicillin", ResistanceClass.BETA_LACTAMS),
        ("carbapenem", ResistanceClass.BETA_LACTAMS),
        ("monobactam", ResistanceClass.BETA_LACTAMS),
        ("glycylcycline", ResistanceClass.GLYCYLCYCLINES),
        ("tigecycline", ResistanceClass.GLYCYLCYCLINES),
        ("tetracycline", ResistanceClass.TETRACYCLINES),
        ("quinolone", ResistanceClass.FLUOROQUINOLONES),
        ("macrolide", ResistanceClass.MACROLIDES),
        ("phenicol", ResistanceClass.PHENICOLS),
        ("chloramphenicol", ResistanceClass.PHENICOLS),
        ("rifamycin", ResistanceClass.RIFAMYCINS),
        ("rifampin", ResistanceClass.RIFAMYCINS),
        ("oxazolidinone", ResistanceClass.OXAZOLIDINONES),
        ("linezolid", ResistanceClass.OXAZOLIDINONES),
        ("lipopeptide", ResistanceClass.LIPOPEPTIDES),
        ("daptomycin", ResistanceClass.LIPOPEPTIDES),
        ("fosfomycin", ResistanceClass.FOSFOMYCIN),
        ("sulfonamide", ResistanceClass.SULFONAMIDES),
        ("sulphonamide", ResistanceClass.SULFONAMIDES),
        ("trimethoprim", ResistanceClass.TRIMETHOPRIM),
        ("diaminopyrimidine", ResistanceClass.TRIMETHOPRIM),
        ("polymyxin", ResistanceClass.POLYMYXINS),
        ("colistin", ResistanceClass.POLYMYXINS),
        ("glycopeptide", ResistanceClass.GLYCOPEPTIDES),
        ("vancomycin", ResistanceClass.GLYCOPEPTIDES),
        ("efflux", ResistanceClass.MULTI_DRUG),
        ("multidrug", ResistanceClass.MULTI_DRUG),
        ("multi-drug", ResistanceClass.MULTI_DRUG),
    ]
    matches = {cls for kw, cls in keywords if kw in s}
    if len(matches) == 1:
        return next(iter(matches))
    if len(matches) > 1:
        return ResistanceClass.MULTI_DRUG
    return ResistanceClass.OTHER


class ConfidenceLevel(str, Enum):
    """Confidence levels for AMR calls."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AMRConfig(BaseModel):
    """Configuration for AMR detection."""

    tools: list[str] = Field(
        default=["card_rgi", "amrfinderplus"],
        description="Tools to run for AMR detection",
    )
    min_coverage_percent: float = Field(default=80.0, ge=0.0, le=100.0)
    min_identity_percent: float = Field(default=95.0, ge=0.0, le=100.0)
    threads: int = Field(default=4, ge=1, le=128)
    enable_consensus: bool = Field(
        default=True, description="Aggregate results from multiple tools"
    )


class AMRHit(BaseModel):
    """Single AMR gene detection hit."""

    gene_name: str
    gene_family: str
    resistance_class: ResistanceClass
    contig_id: str
    start_position: int
    end_position: int
    gene_length: int
    identity_percent: float
    coverage_percent: float
    tool_name: str
    confidence: ConfidenceLevel
    phenotype: Optional[str] = None
    literature_references: list[str] = Field(default_factory=list)


class AMRDetectionResult(BaseModel):
    """Results from AMR detection analysis."""

    detection_id: UUID
    sample_id: UUID
    assembly_id: UUID
    tools_run: list[str]
    total_amr_genes: int
    unique_gene_families: int
    resistance_classes: list[ResistanceClass]
    hits: list[AMRHit] = Field(default_factory=list)
    virulence_hits: list[dict] = Field(default_factory=list)
    mutation_hits: list[dict] = Field(default_factory=list)
    phenotype_summary: dict = Field(
        default_factory=dict, description="Predicted phenotypes"
    )
    confidence_scores: dict = Field(
        default_factory=dict, description="Per-class confidence"
    )
    consensus_hits: list[AMRHit] = Field(
        default_factory=list, description="Hits confirmed by ≥2 tools"
    )
    output_files: dict = Field(default_factory=dict, description="Tool outputs")
    errors: list[str] = Field(default_factory=list)


class BaseAMRDetector:
    """Base class for AMR detection tools."""

    def __init__(self, config: AMRConfig):
        """Initialize detector with config."""
        self.config = config

    def detect(
        self,
        assembly_file: Path,
        output_dir: Path,
        progress_callback=None,
    ) -> AMRDetectionResult:
        """
        Execute AMR detection.

        Args:
            assembly_file: Path to assembly FASTA
            output_dir: Directory for output files
            progress_callback: Optional progress callback

        Returns:
            AMRDetectionResult with AMR hits
        """
        raise NotImplementedError("Subclasses must implement detect()")

    def parse_results(self, output_dir: Path) -> list[AMRHit]:
        """Parse tool output and extract hits."""
        raise NotImplementedError("Subclasses must implement parse_results()")
