"""Mutation-based phenotype rule evaluator - Module 1E v1.0.0"""

from typing import List, Dict, Any
from ..result_models import CandidatePrediction
# In a real setup, ResistanceDeterminant would be imported from mutation_engine
# from backend.mutation_engine.result_models import ResistanceDeterminant

class MutationRuleEngine:
    def __init__(self, rules: List[Dict[str, Any]]):
        self.mut_rules = [r for r in rules if r["rule_type"].startswith("mutation")]

    def evaluate(self, mutations: List[Any]) -> List[CandidatePrediction]:
        candidates = []
        for mut in mutations:
            for rule in self.mut_rules:
                if self._mutation_matches(rule["condition"], mut):
                    # Classification modifier: LIKELY -> confidence * 0.85
                    cls_str = getattr(mut, "classification", "")
                    if hasattr(cls_str, "value"):
                        cls_str = cls_str.value
                    conf_mod = 1.0 if cls_str == "KNOWN_RESISTANCE" else 0.85
                    
                    candidates.append(CandidatePrediction(
                        drug=rule.get("drug", "class-level"),
                        drug_class=rule.get("drug_class", ""),
                        sir=rule["action"],
                        rule_id=rule["rule_id"],
                        evidence_type="mutation",
                        evidence_name=getattr(mut, "mutation_notation", None) or getattr(mut, "gene_name", ""),
                        confidence=rule.get("confidence_weight", 1.0) * getattr(mut, "confidence_score", 1.0) * conf_mod,
                        evidence_level=rule.get("evidence_level", 5),
                        organism=rule.get("organism_scope", None)
                    ))
        return candidates

    def _mutation_matches(self, cond: Dict[str, Any], mut: Any) -> bool:
        if cond["type"] == "mutation_exact":
            # For demonstration, we assume mut has gene_name, and either notation or we parse it
            if getattr(mut, "gene_name", "") != cond.get("gene"):
                return False
            # If the engine provides the notation directly we could parse it, or check properties
            # This is a stub condition
            notation = getattr(mut, "mutation_notation", "") or ""
            return str(cond.get("protein_position")) in notation and cond.get("alt_amino_acid") in notation
            
        if cond["type"] == "mutation_domain":
            return getattr(mut, "gene_name", "") == cond.get("gene")
            
        return False
