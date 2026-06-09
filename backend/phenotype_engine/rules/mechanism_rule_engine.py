"""Mechanism-based phenotype rule evaluator - Module 1E v1.0.0"""

from typing import List, Dict, Any
from ..result_models import CandidatePrediction

class MechanismRuleEngine:
    def __init__(self, rules: List[Dict[str, Any]]):
        self.mech_rules = [r for r in rules if r["rule_type"] == "mechanism"]

    def evaluate(self, mechanisms: List[Any]) -> List[CandidatePrediction]:
        candidates = []
        for mech in mechanisms:
            for rule in self.mech_rules:
                if rule["condition"].get("mechanism_code") == getattr(mech, "mechanism_code", ""):
                    for drug_class in getattr(mech, "drug_classes", []):
                        if rule.get("drug_class") in (None, drug_class):
                            candidates.append(CandidatePrediction(
                                drug=rule.get("drug", "class-level"),
                                drug_class=drug_class,
                                sir=rule["action"],
                                rule_id=rule["rule_id"],
                                evidence_type="mechanism",
                                evidence_name=getattr(mech, "mechanism_name", ""),
                                confidence=rule.get("confidence_weight", 1.0) * getattr(mech, "confidence", 1.0),
                                evidence_level=rule.get("evidence_level", 5),
                                organism=rule.get("organism_scope", None)
                            ))
        return candidates
