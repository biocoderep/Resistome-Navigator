"""Mechanism evidence aggregation - Module 1D v1.0.0"""

from collections import defaultdict
from typing import List, Any

from .result_models import MechanismObject, ConfidenceTier

def _build_mech_object(code: str, data: dict, classifier) -> MechanismObject:
    """Construct a MechanismObject from aggregated data."""
    # Look up the ontology info if possible
    mc = classifier.mech_index.get(code, {})
    name = mc.get("display_name", code)
    drug_classes = mc.get("drug_classes", [])
    
    avg_conf = sum(data["confidences"]) / len(data["confidences"]) if data["confidences"] else 0.0
    tier = ConfidenceTier.HIGH if avg_conf >= 0.8 else ConfidenceTier.MEDIUM if avg_conf >= 0.55 else ConfidenceTier.LOW
    
    return MechanismObject(
        mechanism_code=code,
        mechanism_name=name,
        mechanism_subclass=None,
        drug_classes=drug_classes,
        supporting_genes=list(set(data["genes"])),
        supporting_mutations=list(set(data["mutations"])),
        evidence_sources=list(set(data["sources"])),
        confidence=round(avg_conf, 4),
        confidence_tier=tier
    )

def aggregate_mechanisms(genes: List[Any], mutations: List[Any], mappings: List[Any], classifier: Any) -> List[MechanismObject]:
    """Aggregate gene and mutation findings into unique mechanisms."""
    mech_map = defaultdict(lambda: {"genes":[], "mutations":[], "confidences":[], "sources":[]})
    
    for gene in genes:
        mech = classifier.classify_gene(gene)
        code = mech["code"]
        mech_map[code]["genes"].append(getattr(gene, "gene_name", "Unknown"))
        mech_map[code]["confidences"].append(mech["confidence"])
        mech_map[code]["sources"].append(mech["source"])
        
    for mutation, mapping in zip(mutations, mappings):
        mech = classifier.classify_mutation(mutation, mapping)
        code = mech["code"]
        notation = getattr(mutation, "mutation_notation", "Unknown")
        mech_map[code]["mutations"].append(notation)
        mech_map[code]["confidences"].append(mech["confidence"])
        mech_map[code]["sources"].append(mech["source"])
        
    return [_build_mech_object(code, data, classifier) for code, data in mech_map.items()]
