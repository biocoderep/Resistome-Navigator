"""Duplicate contig detection (Phase 2 MVP stub)."""

from __future__ import annotations

from .models import DuplicateContigReport


def detect_duplicates(contigs: list) -> DuplicateContigReport:
    """Detect exact and near-duplicate contigs (Phase 2).
    
    MVP stub: returns empty report.
    """
    return DuplicateContigReport(
        exact_duplicates=[],
        near_duplicates=[],
        total_duplicate_pairs=0,
        recommendation="Duplicate detection disabled in MVP.",
    )


__all__ = ["detect_duplicates"]
