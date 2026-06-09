"""Novel mutation detection engine - Module 1D v1.0.0"""

from typing import List, Dict, Any
from .result_models import AnnotatedVariant, MutationMapping, MutationClassification, SIRPrediction

def extract_novel_mutations(variants: List[AnnotatedVariant], mappings: List[MutationMapping], sample_id: str) -> Dict[str, Any]:
    """Extract novel mutations and generate a report."""
    novel_list = []
    
    for v, mapping in zip(variants, mappings):
        cls = mapping.classification
        if cls in (MutationClassification.NOVEL_IN_DOMAIN, MutationClassification.NOVEL, MutationClassification.LIKELY_RESISTANCE):
            
            if cls == MutationClassification.NOVEL_IN_DOMAIN:
                sir = SIRPrediction.INDETERMINATE
                notes = f"Position {v.raw_variant.protein_position} is within {v.domain}; not in knowledgebase; requires wet-lab confirmation"
            elif cls == MutationClassification.LIKELY_RESISTANCE:
                sir = SIRPrediction.INTERMEDIATE # Or use inferred from kb
                notes = mapping.kb_entry.get("note", "") if mapping.kb_entry else ""
            else:
                sir = SIRPrediction.UNKNOWN
                notes = f"New position in known resistance gene {v.raw_variant.gene_name}; outside known domains"
                
            novel_list.append({
                "gene": v.raw_variant.gene_name,
                "mutation": v.mutation_notation,
                "position": v.raw_variant.protein_position,
                "domain": v.domain or "None",
                "classification": cls.value,
                "sir_prediction": sir.value,
                "notes": notes
            })
            
    return {
        "sample_id": sample_id,
        "novel_mutations": novel_list,
        "total_novel": len(novel_list)
    }
