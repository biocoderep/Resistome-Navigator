"""Conflict resolution engine - Module 1E v1.0.0"""

from typing import List
from ..result_models import CandidatePrediction, ResolvedPrediction

SIR_PRIORITY = {"R": 3, "I": 2, "S": 1, "INDETERMINATE": 0, "NOT_TESTABLE": -1}

class ConflictResolutionEngine:
    def resolve(self, candidates: List[CandidatePrediction], drug: str) -> ResolvedPrediction:
        """Select winning SIR and track all evidence."""
        drug_candidates = [c for c in candidates if c.drug == drug or c.drug == "class-level"]
        
        if not drug_candidates:
            return ResolvedPrediction(
                drug=drug, sir="NOT_TESTABLE", confidence=0.0,
                winning_rule="", winning_rule_evidence_level=5, winning_rule_weight=0.0,
                all_evidence=[], has_conflict=False
            )
            
        # Sort by SIR priority desc, then evidence_level asc, then confidence desc
        ranked = sorted(drug_candidates,
                        key=lambda c: (-SIR_PRIORITY.get(c.sir, 0), c.evidence_level, -c.confidence))
                        
        winner = ranked[0]
        conflict_flag = len({c.sir for c in ranked}) > 1
        
        return ResolvedPrediction(
            drug=drug, 
            sir=winner.sir,
            confidence=winner.confidence,
            winning_rule=winner.rule_id,
            winning_rule_evidence_level=winner.evidence_level,
            winning_rule_weight=winner.confidence / (winner.confidence or 1.0), # Simplified for stub
            all_evidence=ranked, 
            has_conflict=conflict_flag,
            drug_class=winner.drug_class
        )
