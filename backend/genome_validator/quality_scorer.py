"""Quality scoring engine - composite score calculation."""

from __future__ import annotations

from .models import (
    AmbiguityReport,
    AssemblyMetrics,
    ContaminationReport,
    GenomeSizeReport,
    QualityScoreComponents,
    QualityScoreReport,
)


def compute_quality_score(
    metrics: AssemblyMetrics,
    ambiguity_report: AmbiguityReport,
    genome_size_report: GenomeSizeReport,
    contamination_report: ContaminationReport,
    gc_outlier_count: int = 0,
) -> QualityScoreReport:
    """Compute composite quality score (0-100).
    
    Formula: Q = Σ (weight_i × component_score_i), normalized to 0-100.
    
    Components:
    - N50 relative to genome size (25%)
    - Contig count score (20%)
    - N% score (20%)
    - GC consistency (10%)
    - Contamination score (15%)
    - Complexity score (5%)
    - Assembly size score (5%)
    """
    genome_size_mb = metrics.total_length_bp / 1_000_000
    
    # Component 1: N50 score (25 points max)
    # Score = 100 × min(N50 / (genome_size_bp × 0.02), 1.0)
    expected_n50_bp = metrics.total_length_bp * 0.02
    n50_ratio = min(metrics.n50_bp / expected_n50_bp, 1.0) if expected_n50_bp > 0 else 0.0
    n50_score = n50_ratio * 25.0
    
    # Component 2: Contig count score (20 points max)
    # Score = 100 × max(0, 1 − (contig_count / 1000))
    contig_score_raw = max(0.0, 1.0 - (metrics.contig_count / 1000.0))
    contig_score = contig_score_raw * 20.0
    
    # Component 3: N% score (20 points max)
    if ambiguity_report.n_percent < 1.0:
        n_score = 20.0
    elif ambiguity_report.n_percent < 5.0:
        n_score = 12.0  # 60% of 20
    else:
        n_score = 0.0
    
    # Component 4: GC consistency (10 points max)
    if genome_size_report.size_status == "PASS":
        gc_score = 10.0
    elif genome_size_report.size_status == "WARNING":
        gc_score = 6.0  # 60% of 10
    else:
        gc_score = 0.0
    
    # Component 5: Contamination score (15 points max)
    if contamination_report.risk_level == "LOW_RISK":
        contamination_score = 15.0
    elif contamination_report.risk_level == "MODERATE_RISK":
        contamination_score = 9.0  # 60% of 15
    else:
        contamination_score = 0.0
    
    # Component 6: Complexity score (5 points max, placeholder)
    complexity_score = 5.0
    
    # Component 7: Size score (5 points max)
    if genome_size_report.size_status == "PASS":
        size_score = 5.0
    elif genome_size_report.size_status == "WARNING":
        size_score = 2.5  # 50% of 5
    else:
        size_score = 0.0
    
    # Compute overall score
    overall_score = (
        n50_score
        + contig_score
        + n_score
        + gc_score
        + contamination_score
        + complexity_score
        + size_score
    )
    
    # Classify
    if overall_score >= 85:
        classification = "EXCELLENT"
    elif overall_score >= 70:
        classification = "GOOD"
    elif overall_score >= 55:
        classification = "ACCEPTABLE"
    elif overall_score >= 40:
        classification = "POOR"
    else:
        classification = "FAILED"
    
    return QualityScoreReport(
        overall_score=overall_score,
        classification=classification,
        components=QualityScoreComponents(
            n50_score=n50_score,
            contig_score=contig_score,
            n_percent_score=n_score,
            gc_consistency=gc_score,
            contamination=contamination_score,
            complexity=complexity_score,
            size_score=size_score,
        ),
    )


__all__ = ["compute_quality_score"]
