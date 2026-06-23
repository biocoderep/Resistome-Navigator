"""Pydantic models for all genome validation reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# CONFIG MODELS
# ============================================================================


class ValidationConfig(BaseModel):
    """Configuration for genome validation run."""

    min_length_bp: int = Field(default=200_000, ge=0, le=1_000_000)
    max_contig_count: int = Field(default=2000, ge=1, le=50_000)
    n_fail_threshold: float = Field(default=5.0, ge=1.0, le=50.0)
    n_warn_threshold: float = Field(default=1.0, ge=0.1, le=5.0)
    run_kmer_analysis: bool = False  # Phase 2 feature


# ============================================================================
# ERROR & WARNING MODELS
# ============================================================================


class ValidationError(BaseModel):
    """Single validation error or warning."""

    code: Literal[
        "FILE_EMPTY",
        "NOT_FASTA_FORMAT",
        "MALFORMED_HEADER",
        "DUPLICATE_HEADER",
        "EMPTY_SEQUENCE",
        "INVALID_NUCLEOTIDE",
        "BINARY_CONTENT",
        "ENCODING_ERROR",
        "TRUNCATED_FILE",
        "CONTIG_TOO_SHORT",
        "INVALID_FILE_TYPE",
        "GENOME_TOO_SMALL",
        "GENOME_SMALL",
        "GENOME_TOO_LARGE",
        "GENOME_LARGE",
        "GC_OUTLIERS",
        "UNEXPECTED_ERROR",
        "N_PERCENT_TOO_HIGH",
        "N_PERCENT_WARNING",
        "VALIDATION_ERROR",
        "VALIDATION_WARNING",
    ]
    contig: str | None = None
    detail: str | None = None
    line_number: int | None = None


# ============================================================================
# INTEGRITY MODELS
# ============================================================================


class IntegrityReport(BaseModel):
    """File integrity check results."""

    file_path: str
    file_size_bytes: int
    md5: str
    sha256: str
    is_gzipped: bool
    uncompressed_size: int | None = None
    record_count: int
    encoding: str


# ============================================================================
# ASSEMBLY STATISTICS MODELS
# ============================================================================


class AssemblyMetrics(BaseModel):
    """Complete assembly statistics."""

    sample_id: UUID
    assembly_id: UUID | None = None
    total_length_bp: int
    contig_count: int
    mean_contig_bp: float
    median_contig_bp: float
    max_contig_bp: int
    min_contig_bp: int
    n50_bp: int
    n90_bp: int
    l50: int
    gc_percent: float
    n_percent: float
    assembly_span_bp: int
    computed_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# GC ANALYSIS MODELS
# ============================================================================


class PerContigGC(BaseModel):
    """Per-contig GC content."""

    contig_id: str
    length: int
    gc_pct: float


class GCOutlier(BaseModel):
    """GC outlier contig."""

    contig_id: str
    length: int
    gc_pct: float
    deviation_sd: float


class GCAnalysisReport(BaseModel):
    """GC content analysis results."""

    whole_genome_gc_pct: float
    mean_contig_gc_pct: float
    gc_variance: float
    gc_std_dev: float
    per_contig: list[PerContigGC]
    outlier_contigs: list[GCOutlier]
    flag: Literal["OK", "CONTAMINATION_SUSPECTED", "WARNING"] = "OK"
    flag_reason: str | None = None


# ============================================================================
# AMBIGUITY ANALYSIS MODELS
# ============================================================================


class PerContigAmbiguity(BaseModel):
    """Per-contig N and ambiguity content."""

    contig_id: str
    n_count: int
    n_pct: float


class NRun(BaseModel):
    """N-run location."""

    contig_id: str
    run_length: int
    position: int


class AmbiguityReport(BaseModel):
    """Ambiguous base analysis."""

    total_bases: int
    n_count: int
    n_percent: float
    n_status: Literal["PASS", "WARNING", "FAIL"]
    longest_n_run: NRun | None = None
    per_contig_n: list[PerContigAmbiguity]
    other_ambiguity_pct: float


# ============================================================================
# CONTIG ANALYSIS MODELS
# ============================================================================


class ContigReport(BaseModel):
    """Contig fragmentation and length analysis."""

    contig_count: int
    fragmentation_class: Literal["EXCELLENT", "ACCEPTABLE", "POOR", "HIGHLY_FRAGMENTED"]
    length_distribution: dict[str, int]  # e.g., {"0-500": 3, "500-1000": 8, ...}
    short_contig_count_below_500bp: int


# ============================================================================
# DUPLICATE CONTIG MODELS
# ============================================================================


class ExactDuplicate(BaseModel):
    """Exact duplicate pair."""

    contig_a: str
    contig_b: str
    type: Literal["EXACT"] = "EXACT"


class NearDuplicate(BaseModel):
    """Near-duplicate pair (>95% similarity)."""

    contig_a: str
    contig_b: str
    jaccard: float
    type: Literal["NEAR"] = "NEAR"


class DuplicateContigReport(BaseModel):
    """Duplicate contig detection."""

    exact_duplicates: list[ExactDuplicate]
    near_duplicates: list[NearDuplicate]
    total_duplicate_pairs: int
    recommendation: str = "No duplicates detected."


# ============================================================================
# COMPLEXITY ANALYSIS MODELS (Phase 2)
# ============================================================================


class LowComplexityContig(BaseModel):
    """Low-complexity contig details."""

    contig_id: str
    entropy: float
    reason: str


class Homopolymer(BaseModel):
    """Homopolymer run."""

    base: Literal["A", "T", "G", "C", "N"]
    length: int
    contig_id: str
    position: int


class ComplexityReport(BaseModel):
    """Sequence complexity analysis (Phase 2)."""

    mean_shannon_entropy: float = 0.0
    min_contig_entropy: float = 0.0
    low_complexity_contigs: list[LowComplexityContig] = []
    total_homopolymer_runs: int = 0
    longest_homopolymer: Homopolymer | None = None


# ============================================================================
# K-MER ANALYSIS MODELS (Phase 2)
# ============================================================================


class KmerSpectrum(BaseModel):
    """K-mer spectrum for single k value."""

    k: int
    total_kmers: int
    unique_kmers: int
    singleton_pct: float
    coverage_estimate: float


class KmerReport(BaseModel):
    """K-mer analysis report (Phase 2)."""

    k21: KmerSpectrum | None = None
    k31: KmerSpectrum | None = None
    k51: KmerSpectrum | None = None
    contamination_signals: list[str] = []
    assembly_completeness_estimate: Literal["HIGH", "MEDIUM", "LOW"] = "HIGH"


# ============================================================================
# GENOME SIZE MODELS
# ============================================================================


class GenomeSizeReport(BaseModel):
    """Genome size validation."""

    assembly_size_mb: float
    expected_min_mb: float
    expected_max_mb: float
    size_status: Literal["PASS", "WARNING", "FAIL"]
    size_percentile_for_species: float = 0.0


# ============================================================================
# TAXONOMY CONSISTENCY MODELS (Phase 2)
# ============================================================================


class TaxonomyConsistencyReport(BaseModel):
    """Taxonomic consistency check (Phase 2)."""

    registered_species: str | None = None
    mash_predicted_species: str | None = None
    mash_confidence: float = 0.0
    mash_distance: float = 0.0
    gc_expected_range: list[float] | None = None
    gc_observed: float = 0.0
    gc_consistent: bool = True
    size_expected_range_mb: list[float] | None = None
    size_observed_mb: float = 0.0
    size_consistent: bool = True
    taxonomy_status: Literal["CONSISTENT", "WARNING", "MISMATCH"] = "CONSISTENT"


# ============================================================================
# CONTAMINATION MODELS (Phase 2)
# ============================================================================


class ContaminationSignal(BaseModel):
    """Single contamination signal."""

    signal_type: str
    detection_method: str
    weight: Literal["LOW", "MEDIUM", "HIGH"]
    detail: str | None = None


class ContaminationReport(BaseModel):
    """Contamination risk assessment (Phase 2)."""

    risk_level: Literal["LOW_RISK", "MODERATE_RISK", "HIGH_RISK"] = "LOW_RISK"
    signals_detected: int = 0
    signals: list[ContaminationSignal] = []
    gc_outlier_contigs: list[str] = []
    bimodal_gc: bool = False
    taxonomy_mismatch: bool = False
    recommendation: str = "No contamination signals detected. Proceed with analysis."


# ============================================================================
# QUALITY SCORE MODELS
# ============================================================================


class QualityScoreComponents(BaseModel):
    """Individual component scores for quality assessment."""

    n50_score: float
    contig_score: float
    n_percent_score: float
    gc_consistency: float
    contamination: float
    complexity: float
    size_score: float


class QualityScoreReport(BaseModel):
    """Composite quality score."""

    overall_score: float
    classification: Literal["EXCELLENT", "GOOD", "ACCEPTABLE", "POOR", "FAILED"]
    components: QualityScoreComponents
    computed_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# VALIDATION STATUS (FINAL DECISION)
# ============================================================================


class ValidationStatus(BaseModel):
    """Final validation decision."""

    sample_id: UUID
    assembly_id: UUID | None = None
    status: Literal["PASS", "WARNING", "FAIL"]
    quality_class: Literal["EXCELLENT", "GOOD", "ACCEPTABLE", "POOR", "FAILED"]
    quality_score: float
    fail_reasons: list[str] = []
    warnings: list[str] = []
    override_status: Literal["USER_OVERRIDE", "ADMIN_OVERRIDE"] | None = None
    override_by: str | None = None
    override_at: datetime | None = None
    proceed_to_amr: bool
    confidence_cap: Literal["FULL", "MEDIUM", "LOW"]


# ============================================================================
# MASTER VALIDATION REPORT
# ============================================================================


class ValidationReport(BaseModel):
    """Master validation report combining all sub-reports."""

    job_id: UUID
    sample_id: UUID
    assembly_id: UUID | None = None
    validation_status: Literal["PASS", "WARNING", "FAIL"]
    quality_score: float
    quality_class: Literal["EXCELLENT", "GOOD", "ACCEPTABLE", "POOR", "FAILED"]
    proceed_to_amr: bool
    confidence_cap: Literal["FULL", "MEDIUM", "LOW"]
    errors: list[ValidationError] = []
    warnings: list[ValidationError] = []
    assembly_metrics: AssemblyMetrics | None = None
    gc_analysis: GCAnalysisReport | None = None
    ambiguity_report: AmbiguityReport | None = None
    contig_report: ContigReport | None = None
    duplicate_contig_report: DuplicateContigReport | None = None
    complexity_report: ComplexityReport | None = None
    kmer_report: KmerReport | None = None
    genome_size_report: GenomeSizeReport | None = None
    taxonomy_report: TaxonomyConsistencyReport | None = None
    contamination_report: ContaminationReport | None = None
    quality_score_detail: QualityScoreReport | None = None
    computed_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# API REQUEST/RESPONSE MODELS
# ============================================================================


class ValidationRequest(BaseModel):
    """API request to start validation."""

    sample_id: UUID
    file_id: UUID
    assembly_id: UUID | None = None
    config: ValidationConfig = Field(default_factory=ValidationConfig)


class ValidationJobResponse(BaseModel):
    """Response when submitting validation job."""

    status: Literal["success", "error"]
    data: dict[str, Any] = Field(default_factory=dict)


class ValidationStatusResponse(BaseModel):
    """Poll job status response."""

    job_id: UUID
    sample_id: UUID
    status: Literal["QUEUED", "RUNNING", "COMPLETED", "FAILED"]
    progress_pct: int = 0
    current_step: str = ""
    error_message: str | None = None


class ValidationResultsResponse(BaseModel):
    """Full validation results response."""

    job_id: UUID
    validation_status: Literal["PASS", "WARNING", "FAIL"]
    quality_score: float
    quality_class: Literal["EXCELLENT", "GOOD", "ACCEPTABLE", "POOR", "FAILED"]
    proceed_to_amr: bool
    confidence_cap: Literal["FULL", "MEDIUM", "LOW"]
    assembly_metrics: AssemblyMetrics | None = None
    gc_analysis: GCAnalysisReport | None = None
    ambiguity_report: AmbiguityReport | None = None
    contig_report: ContigReport | None = None
    duplicate_contig_report: DuplicateContigReport | None = None
    complexity_report: ComplexityReport | None = None
    kmer_report: KmerReport | None = None
    genome_size_report: GenomeSizeReport | None = None
    taxonomy_report: TaxonomyConsistencyReport | None = None
    contamination_report: ContaminationReport | None = None
    quality_score_detail: QualityScoreReport | None = None
    report_files: list[dict[str, str]] = []


# ============================================================================
# DATA CLASSES FOR INTERNAL OPERATIONS
# ============================================================================


@dataclass
class ContigData:
    """Internal contig representation."""

    contig_id: str
    sequence: str
    length: int
    gc_pct: float
    n_pct: float
    entropy: float


__all__ = [
    "ValidationConfig",
    "ValidationError",
    "IntegrityReport",
    "AssemblyMetrics",
    "GCAnalysisReport",
    "AmbiguityReport",
    "ContigReport",
    "DuplicateContigReport",
    "ComplexityReport",
    "KmerReport",
    "GenomeSizeReport",
    "TaxonomyConsistencyReport",
    "ContaminationReport",
    "QualityScoreReport",
    "ValidationStatus",
    "ValidationReport",
    "ValidationRequest",
    "ValidationResultsResponse",
]
