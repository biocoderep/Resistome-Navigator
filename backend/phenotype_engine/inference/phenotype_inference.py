"""Phenotype prediction orchestrator - Module 1E v1.0.0"""

from typing import List, Dict, Any, Optional
from ..result_models import PhenotypePrediction, CandidatePrediction, AMRGeneResult
from ..rules.gene_rule_engine import GeneRuleEngine
from ..rules.mutation_rule_engine import MutationRuleEngine
from ..rules.mechanism_rule_engine import MechanismRuleEngine
from ..rules.combinatorial_rules import CombinatorialRuleEngine
from .conflict_resolution import ConflictResolutionEngine
from .inheritance_engine import InheritanceEngine
from .confidence_propagation import ConfidencePropagator
from ..explanation_engine import generate_explanation

class PhenotypeInferenceEngine:
    def __init__(self, rule_repo, breakpoint_adapter, confidence_propagator):
        self.gene_engine = GeneRuleEngine(rule_repo.gene_rules)
        self.mut_engine = MutationRuleEngine(rule_repo.mutation_rules)
        self.mech_engine = MechanismRuleEngine(rule_repo.mechanism_rules)
        self.combo_engine = CombinatorialRuleEngine(rule_repo.combo_rules, self.gene_engine, self.mut_engine, self.mech_engine)
        
        self.resolver = ConflictResolutionEngine()
        self.inheritance = InheritanceEngine()
        self.bp_adapter = breakpoint_adapter
        self.conf_prop = confidence_propagator

    def predict(self, sample_id: str, assembly_quality: str, 
                genes: List[AMRGeneResult], mutations: List[Any], mechanisms: List[Any],
                species: Optional[str] = None, breakpoint_source: str = "EUCAST") -> List[PhenotypePrediction]:
                
        # 1. Evaluate all rule types
        candidates = (
            self.gene_engine.evaluate(genes) +
            self.mut_engine.evaluate(mutations) +
            self.mech_engine.evaluate(mechanisms) +
            self.combo_engine.evaluate(genes, mutations, mechanisms)
        )
        
        # 2. Get all drugs with at least one candidate
        drugs = {c.drug for c in candidates if c.drug != "class-level"}
        # Include drugs from class-level rules (simplified here for demonstration)
        # In a real scenario we'd map drug_class -> specific drugs via ontology
        if not drugs and candidates:
             drugs = {c.drug_class for c in candidates}

        # 3. Resolve conflicts per drug
        predictions = []
        for drug in drugs:
            # Apply inheritance (simplified)
            inherited_candidates = [c for c in candidates if c.drug == drug or c.drug_class == drug]
            
            resolved = self.resolver.resolve(inherited_candidates, drug)
            if resolved.sir == "NOT_TESTABLE":
                continue
                
            conf = self.conf_prop.propagate(resolved, assembly_quality, breakpoint_source)
            
            # Breakpoint lookup (stubbed)
            bp_version = "EUCAST v13" if breakpoint_source == "EUCAST" else "CLSI M100"
            
            pred = PhenotypePrediction(
                prediction_id=f"pred_{sample_id}_{drug}",
                sample_id=sample_id,
                drug=drug,
                drug_class=resolved.drug_class,
                antibiotic_class=resolved.drug_class,
                predicted_sir=resolved.sir,
                confidence_score=conf["confidence"],
                confidence_tier=conf["tier"],
                breakpoint_source=breakpoint_source,
                breakpoint_version=bp_version,
                is_not_testable=False,
                has_conflict=resolved.has_conflict,
                supporting_genes=[c.evidence_name for c in resolved.all_evidence if c.evidence_type == "gene"],
                supporting_mutations=[c.evidence_name for c in resolved.all_evidence if c.evidence_type == "mutation"],
                supporting_mechanisms=[c.evidence_name for c in resolved.all_evidence if c.evidence_type == "mechanism"],
                supporting_rules=[c.rule_id for c in resolved.all_evidence],
                all_candidates=resolved.all_evidence
            )
            pred.explanation = generate_explanation(pred)
            predictions.append(pred)
            
        return predictions
