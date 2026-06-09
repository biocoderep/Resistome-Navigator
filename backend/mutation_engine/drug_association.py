"""Drug resistance association engine - Module 1D v1.0.0"""

from typing import List, Dict, Any
from .result_models import DrugAssociation, SIRPrediction, ResistanceDeterminant

# Cross-resistance rules
CROSS_RESISTANCE = {
    "fluoroquinolone": ["ciprofloxacin", "levofloxacin", "moxifloxacin", "norfloxacin"],
    "beta-lactam": ["ampicillin", "piperacillin", "cefazolin", "ceftriaxone"],
    "carbapenem": ["meropenem", "imipenem", "ertapenem", "doripenem"],
    "aminoglycoside": ["gentamicin", "tobramycin", "amikacin", "kanamycin"],
    "glycopeptide": ["vancomycin", "teicoplanin"],
    "polymyxin": ["colistin", "polymyxin B"],
    "rifamycin": ["rifampicin"]
}

def associate_drugs(determinants: List[ResistanceDeterminant]) -> List[DrugAssociation]:
    """Generate drug associations based on resistance determinants."""
    associations = []
    
    for det in determinants:
        drug_class = det.drug_class.lower()
        cross_res = CROSS_RESISTANCE.get(drug_class, [])
        
        # Primary drug (simplified: taking the first from cross resistance list if none specified)
        primary_drug = cross_res[0] if cross_res else f"unknown {drug_class}"
        
        # Cross resistance (all others in the class)
        cross_res_list = [d for d in cross_res if d != primary_drug]
        
        evidence_name = det.mutation_notation if det.mutation_notation else det.gene_name
        
        assoc = DrugAssociation(
            drug_name=primary_drug,
            drug_class=drug_class,
            sir_prediction=det.sir_prediction,
            evidence_type=det.determinant_type,
            evidence_name=evidence_name,
            evidence_level=det.evidence_level,
            confidence=det.confidence_score,
            cross_resistance=cross_res_list
        )
        associations.append(assoc)
        
    return associations
