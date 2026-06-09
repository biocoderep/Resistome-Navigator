"""Genome Validation Engine - MVP implementation.

This module provides complete genome assembly validation for the AMR Platform.
"""

from .engine import GenomeValidationEngine
from .models import (
    AmbiguityReport,
    AssemblyMetrics,
    ContaminationReport,
    DuplicateContigReport,
    GCAnalysisReport,
    GenomeSizeReport,
    QualityScoreReport,
    TaxonomyConsistencyReport,
    ValidationConfig,
    ValidationError,
    ValidationReport,
    ValidationStatus,
)

__version__ = "1.0.0"

__all__ = [
    "GenomeValidationEngine",
    "ValidationConfig",
    "ValidationError",
    "AssemblyMetrics",
    "GCAnalysisReport",
    "AmbiguityReport",
    "DuplicateContigReport",
    "GenomeSizeReport",
    "TaxonomyConsistencyReport",
    "ContaminationReport",
    "QualityScoreReport",
    "ValidationStatus",
    "ValidationReport",
]
