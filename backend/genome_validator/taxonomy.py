"""Taxonomic consistency check (Phase 2 MVP stub)."""

from .models import TaxonomyConsistencyReport


def check_taxonomy(
    species: str | None = None,
    gc_pct: float = 0.0,
    assembly_size_mb: float = 0.0,
) -> TaxonomyConsistencyReport:
    """Check taxonomic consistency (Phase 2).
    
    MVP stub: returns basic report without Mash analysis.
    """
    return TaxonomyConsistencyReport(
        registered_species=species,
        mash_predicted_species=species,
        mash_confidence=0.0,
        mash_distance=0.0,
        gc_observed=gc_pct,
        gc_consistent=True,
        size_observed_mb=assembly_size_mb,
        size_consistent=True,
        taxonomy_status="CONSISTENT",
    )


__all__ = ["check_taxonomy"]
