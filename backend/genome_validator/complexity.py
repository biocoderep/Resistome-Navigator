"""Sequence complexity analysis (Phase 2 MVP stub)."""

from .models import ComplexityReport


def analyze_complexity(contigs: list) -> ComplexityReport:
    """Analyze sequence complexity including Shannon entropy (Phase 2).
    
    MVP stub: returns empty report.
    """
    return ComplexityReport(
        mean_shannon_entropy=0.0,
        min_contig_entropy=0.0,
        low_complexity_contigs=[],
        total_homopolymer_runs=0,
        longest_homopolymer=None,
    )


__all__ = ["analyze_complexity"]
