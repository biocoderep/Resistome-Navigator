"""Contamination screening (Phase 2 MVP stub)."""

from .models import ContaminationReport


def screen_contamination(
    gc_outlier_count: int = 0,
    taxonomy_mismatch: bool = False,
    assembly_size_mb: float = 0.0,
) -> ContaminationReport:
    """Screen for contamination signals (Phase 2).
    
    MVP stub: returns basic risk assessment without full analysis.
    """
    risk_level = "LOW_RISK"
    
    if taxonomy_mismatch or assembly_size_mb > 10.0:
        risk_level = "HIGH_RISK"
    elif gc_outlier_count >= 1:
        risk_level = "MODERATE_RISK"
    
    return ContaminationReport(
        risk_level=risk_level,
        signals_detected=0,
        signals=[],
        gc_outlier_contigs=[],
        bimodal_gc=False,
        taxonomy_mismatch=taxonomy_mismatch,
        recommendation=f"Contamination risk: {risk_level}. Proceed with analysis.",
    )


__all__ = ["screen_contamination"]
