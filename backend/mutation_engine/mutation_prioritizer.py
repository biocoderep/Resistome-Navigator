"""Mutation prioritisation engine - Module 1D v1.0.0"""

from typing import List, Dict
from .result_models import ResistanceDeterminant

# Hardcoded lists for priority scoring
CRITICAL_DRUGS = {"carbapenem", "glycopeptide", "polymyxin"}
HIGH_PRIORITY_DRUGS = {"fluoroquinolone", "beta-lactam", "cephalosporin"}

def compute_priority_score(determinant: ResistanceDeterminant) -> float:
    """Compute priority score for a resistance determinant."""
    # Clinical relevance (based on drug_class for simplicity in stub)
    drug_class = determinant.drug_class.lower()
    if drug_class in CRITICAL_DRUGS:
        clin_rel = 1.0
        drug_imp = 1.0
    elif drug_class in HIGH_PRIORITY_DRUGS:
        clin_rel = 0.70
        drug_imp = 0.80
    else:
        clin_rel = 0.40
        drug_imp = 0.60
        
    conf_score = determinant.confidence_score
    
    ev_level = determinant.evidence_level
    if ev_level <= 2:
        ev_str = 1.0
    elif ev_level == 3:
        ev_str = 0.70
    else:
        ev_str = 0.40
        
    p_score = 0.35 * clin_rel + 0.25 * drug_imp + 0.25 * conf_score + 0.15 * ev_str
    return round(p_score, 4)

def rank_mutations(determinants: List[ResistanceDeterminant]) -> List[ResistanceDeterminant]:
    """Rank mutations by priority score in place."""
    for det in determinants:
        det.priority_score = compute_priority_score(det)
        
    return sorted(determinants, key=lambda x: x.priority_score, reverse=True)
