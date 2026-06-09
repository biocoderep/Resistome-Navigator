"""Mutation confidence engine - Module 1D v1.0.0"""

from typing import Dict, Optional
from .result_models import AnnotatedVariant, MutationMapping, MutationConfidence, ConfidenceTier, MutationClassification
from .gene_localization import GeneLocation

CLASSIFICATION_WEIGHT = {
    MutationClassification.KNOWN_RESISTANCE: 1.0,
    MutationClassification.LIKELY_RESISTANCE: 0.70,
    MutationClassification.NOVEL_IN_DOMAIN: 0.40,
    MutationClassification.NOVEL: 0.20,
    MutationClassification.UNKNOWN: 0.10,
    MutationClassification.SILENT: 0.10,
}

def _kb_evidence_score(kb_entry: Optional[Dict]) -> float:
    if kb_entry is None:
        return 0.10
    level = kb_entry.get("evidence_level", 5)
    return max(0.0, 1.0 - (level - 1) * 0.15)

def compute_mutation_confidence(variant: AnnotatedVariant, 
                                mapping: MutationMapping,
                                gene_loc: GeneLocation) -> MutationConfidence:
    """Compute confidence score for a variant mapping."""
    aln_q = variant.raw_variant.alignment_quality
    kb_ev = _kb_evidence_score(mapping.kb_entry)
    cov_s = min(gene_loc.coverage_pct / 100.0, 1.0)
    cls_s = CLASSIFICATION_WEIGHT.get(mapping.classification, 0.10)
    
    score = 0.30 * aln_q + 0.35 * kb_ev + 0.20 * cov_s + 0.15 * cls_s
    
    tier = ConfidenceTier.LOW
    if score >= 0.80:
        tier = ConfidenceTier.HIGH
    elif score >= 0.55:
        tier = ConfidenceTier.MEDIUM
        
    return MutationConfidence(
        alignment_quality=aln_q,
        kb_evidence=kb_ev,
        gene_coverage=cov_s,
        classification_score=cls_s,
        final_score=round(score, 4),
        confidence_tier=tier
    )
