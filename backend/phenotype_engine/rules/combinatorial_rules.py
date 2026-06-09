"""Combinatorial rule evaluator - Module 1E v1.0.0"""

from typing import List, Dict, Any
from ..result_models import CandidatePrediction

class CombinatorialRuleEngine:
    def __init__(self, rules: List[Dict[str, Any]], gene_engine, mut_engine, mech_engine):
        self.combo_rules = [r for r in rules if r["rule_type"] == "combinatorial"]
        self.gene_engine = gene_engine
        self.mut_engine = mut_engine
        self.mech_engine = mech_engine

    def evaluate(self, genes: List[Any], mutations: List[Any], mechanisms: List[Any]) -> List[CandidatePrediction]:
        candidates = []
        for rule in self.combo_rules:
            cond = rule["condition"]
            
            if cond["type"] == "all_of":
                if all(self._check(c, genes, mutations, mechanisms) for c in cond.get("conditions", [])):
                    candidates.append(self._make_candidate(rule, genes, mutations))
            
            elif cond["type"] == "any_of":
                if any(self._check(c, genes, mutations, mechanisms) for c in cond.get("conditions", [])):
                    candidates.append(self._make_candidate(rule, genes, mutations))
                    
        return candidates

    def _check(self, cond: Dict[str, Any], genes: List[Any], mutations: List[Any], mechanisms: List[Any]) -> bool:
        if cond["type"].startswith("mutation"):
            return any(self.mut_engine._mutation_matches(cond, mut) for mut in mutations)
        if cond["type"].startswith("gene"):
            return any(self.gene_engine._condition_met(cond, g) for g in genes)
        if cond["type"] == "mechanism":
            return any(getattr(m, "mechanism_code", "") == cond.get("mechanism_code") for m in mechanisms)
        return False

    def _make_candidate(self, rule: Dict[str, Any], genes: List[Any], mutations: List[Any]) -> CandidatePrediction:
        # In a real implementation we would dynamically build the evidence name based on what matched
        return CandidatePrediction(
            drug=rule.get("drug", "class-level"),
            drug_class=rule.get("drug_class", ""),
            sir=rule["action"],
            rule_id=rule["rule_id"],
            evidence_type="combo",
            evidence_name="Combinatorial evidence",
            confidence=rule.get("confidence_weight", 1.0),
            evidence_level=rule.get("evidence_level", 1),
            organism=rule.get("organism_scope", None)
        )
