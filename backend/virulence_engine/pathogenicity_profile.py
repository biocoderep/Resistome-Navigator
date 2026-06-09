"""Pathogenicity Profile Engine - Module 1F v1.0.0"""

from typing import List
from .result_models import VirulenceFactor, PathogenicityProfile

def compute_pathogenicity_profile(sample_id: str, factors: List[VirulenceFactor]) -> PathogenicityProfile:
    categories = {f.category_code for f in factors}
    hr_genes = [f for f in factors if f.is_high_risk]
    
    # Mathematical score limits defined in spec
    burden_s = min(len(factors) / 20.0, 1.0) * 100.0
    diversity_s = min(len(categories) / 12.0, 1.0) * 100.0
    hr_s = min(len(hr_genes) / 5.0, 1.0) * 100.0
    
    score = 0.35 * burden_s + 0.30 * diversity_s + 0.35 * hr_s
    
    cls = "CRITICAL" if score >= 75 else "HIGH" if score >= 50 else "MODERATE" if score >= 25 else "LOW"
    
    cat_summary = {}
    for f in factors:
        cat_summary[f.category_code] = cat_summary.get(f.category_code, 0) + 1
        
    return PathogenicityProfile(
        sample_id=sample_id,
        total_vf_genes=len(factors),
        categories_detected=list(categories),
        category_diversity=len(categories),
        high_risk_count=len(hr_genes),
        high_risk_genes=[f.gene_name for f in hr_genes],
        unique_determinants=[], # simplified
        risk_score=round(score, 2),
        risk_class=cls,
        category_summary=cat_summary,
        confidence=0.0 # Will be populated by confidence framework
    )
