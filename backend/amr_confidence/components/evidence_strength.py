"""Evidence Strength component - amr_confidence v1.0.0"""

from typing import List

EVIDENCE_WEIGHTS = {
    "experimental": 1.00,
    "clinical": 0.95,
    "computational": 0.70,
    "inferred": 0.50,
    "unknown": 0.30,
}

def evidence_strength_score(evidence_types: List[str]) -> float:
    if not evidence_types:
        return EVIDENCE_WEIGHTS["unknown"]
    return max(EVIDENCE_WEIGHTS.get(e, 0.30) for e in evidence_types)
