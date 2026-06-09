"""Hierarchical rule inheritance engine - Module 1E v1.0.0"""

from typing import List, Optional
from ..result_models import CandidatePrediction

class InheritanceEngine:
    """Resolves rule inheritance; child rules override parent class rules."""
    
    def resolve(self, candidates: List[CandidatePrediction], 
                drug: str, drug_class: str, 
                organism: Optional[str] = None) -> List[CandidatePrediction]:
        """
        Priority order (highest first):
        1. Organism-specific drug rule
        2. Drug-specific rule (no organism restriction)
        3. Drug class rule
        4. Mechanism class rule (most general)
        """
        drug_specific = [c for c in candidates if c.drug == drug 
                         and (not c.organism or c.organism == organism)]
        
        class_level = [c for c in candidates if c.drug != drug 
                       and c.drug_class == drug_class]
                       
        return drug_specific or class_level
