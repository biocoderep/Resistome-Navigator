"""Gene-based phenotype rule evaluator - Module 1E v1.0.0"""

from typing import List, Dict, Any
from ..result_models import CandidatePrediction, AMRGeneResult

class GeneRuleEngine:
    def __init__(self, rules: List[Dict[str, Any]]):
        self.gene_rules = [r for r in rules if r["rule_type"] in ("gene", "gene_family")]

    def evaluate(self, genes: List[AMRGeneResult]) -> List[CandidatePrediction]:
        candidates = []
        for gene in genes:
            for rule in self.gene_rules:
                if self._condition_met(rule["condition"], gene):
                    candidates.append(CandidatePrediction(
                        drug=rule.get("drug", "class-level"),
                        drug_class=rule.get("drug_class", ""),
                        sir=rule["action"],
                        rule_id=rule["rule_id"],
                        evidence_type="gene",
                        evidence_name=gene.gene_name,
                        confidence=rule.get("confidence_weight", 1.0) * gene.confidence_score,
                        evidence_level=rule.get("evidence_level", 5),
                        organism=rule.get("organism_scope", None)
                    ))
        return candidates

    def _condition_met(self, cond: Dict[str, Any], gene: AMRGeneResult) -> bool:
        if cond["type"] == "gene_family_match":
            return (gene.gene_family == cond.get("gene_family") and
                    gene.hit_type in cond.get("hit_types", ["Perfect", "Strict", "Loose"]) and
                    gene.identity_pct >= cond.get("min_identity", 80.0) and
                    gene.coverage_pct >= cond.get("min_coverage", 60.0))
        if cond["type"] == "gene_exact":
            return gene.gene_name == cond.get("gene_name")
        return False
