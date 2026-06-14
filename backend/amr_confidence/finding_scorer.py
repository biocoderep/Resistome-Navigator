"""Per-finding confidence scoring helper.

Wraps :func:`amr_confidence.confidence_aggregation.aggregate` so each detected
finding (AMR gene, mutation, virulence factor, phenotype) is scored once and
returned in a shape ready for both the pipeline report and the
``ConfidenceScore`` ORM model (``context``, ``target_name``, ``overall_score``,
``tier``, ``cap_applied``, ``components``, ``weighted``).
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .confidence_aggregation import aggregate, CONTEXT_WEIGHTS

VALID_CONTEXTS = set(CONTEXT_WEIGHTS.keys())  # amr_gene, virulence, mutation, phenotype


def score_finding(
    target_name: str,
    context: str,
    identity_pct: float = 0.0,
    coverage_pct: float = 0.0,
    bit_score: float = 0.0,
    e_value: float = 1.0,
    supporting_tools: Optional[List[str]] = None,
    evidence_types: Optional[List[str]] = None,
    genome_quality: str = "FULL",
    reference_length: int = 1000,
) -> Dict:
    """Score a single finding and return a report/ORM-ready dict.

    Args:
        target_name: Identifier for the finding (gene symbol, mutation notation,
            drug name, virulence gene).
        context: One of ``amr_gene``, ``mutation``, ``virulence``, ``phenotype``.
        genome_quality: Assembly quality class used to cap confidence
            (``FULL``/``PARTIAL``/``DRAFT``) per the genome-quality modifier.
    """
    ctx = context if context in VALID_CONTEXTS else "amr_gene"
    result = aggregate(
        identity_pct=identity_pct,
        coverage_pct=coverage_pct,
        bit_score=bit_score,
        e_value=e_value,
        supporting_tools=supporting_tools or [],
        evidence_types=evidence_types or [],
        context=ctx,
        genome_quality=genome_quality,
        reference_length=reference_length,
    )
    return {
        "context": ctx,
        "target_name": target_name,
        "overall_score": result.overall_score,
        "tier": result.tier,
        "cap_applied": result.cap_applied,
        "components": result.components,
        "weighted": result.weighted,
    }


__all__ = ["score_finding", "VALID_CONTEXTS"]
