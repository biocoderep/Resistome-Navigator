"""Global confidence aggregation engine - amr_confidence v1.0.0"""

from dataclasses import dataclass
from typing import List, Dict, Any

from .components.identity_score import identity_score
from .components.coverage_score import coverage_score
from .components.bitscore_score import bitscore_score
from .components.evalue_score import evalue_score
from .components.agreement_score import agreement_score
from .components.evidence_strength import evidence_strength_score
from .modifiers.genome_quality_modifier import GENOME_CAP

CONTEXT_WEIGHTS = {
    "amr_gene": {"identity":0.30,"coverage":0.25,"bitscore":0.05,"evalue":0.05,"agreement":0.25,"evidence":0.10},
    "virulence": {"identity":0.30,"coverage":0.25,"bitscore":0.05,"evalue":0.05,"agreement":0.20,"evidence":0.15},
    "mutation": {"identity":0.35,"coverage":0.20,"bitscore":0.05,"evalue":0.05,"agreement":0.20,"evidence":0.15},
    "phenotype": {"identity":0.15,"coverage":0.15,"bitscore":0.05,"evalue":0.05,"agreement":0.20,"evidence":0.40},
}

@dataclass
class ConfidenceResult:
    overall_score: float
    tier: str
    components: Dict[str, float]
    weighted: Dict[str, float]
    cap_applied: bool
    context: str

def aggregate(identity_pct: float, coverage_pct: float,
              bit_score: float, e_value: float,
              supporting_tools: List[str], evidence_types: List[str],
              context: str = "amr_gene",
              genome_quality: str = "FULL",
              reference_length: int = 1000) -> ConfidenceResult:
              
    w = CONTEXT_WEIGHTS.get(context, CONTEXT_WEIGHTS["amr_gene"])
    
    comps = {
        "identity": identity_score(identity_pct),
        "coverage": coverage_score(coverage_pct),
        "bitscore": bitscore_score(bit_score, reference_length=reference_length),
        "evalue": evalue_score(e_value),
        "agreement": agreement_score(supporting_tools),
        "evidence": evidence_strength_score(evidence_types),
    }
    
    weighted = {k: w[k] * v for k, v in comps.items()}
    raw = sum(weighted.values())
    
    cap = GENOME_CAP.get(genome_quality, 0.50)
    final = min(raw, cap)
    
    tier = "HIGH" if final >= 0.85 else "MEDIUM" if final >= 0.60 else "LOW"
    
    return ConfidenceResult(
        overall_score=round(final, 3), 
        tier=tier, 
        components={k: round(v, 3) for k, v in comps.items()}, 
        weighted={k: round(v, 3) for k, v in weighted.items()}, 
        cap_applied=(final < raw), 
        context=context
    )
