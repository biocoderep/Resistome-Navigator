"""Confidence propagation engine - Module 1E v1.0.0"""

from typing import Dict, Any
from ..result_models import ResolvedPrediction

EVIDENCE_LEVEL_MODIFIER = {1: 1.00, 2: 0.90, 3: 0.75, 4: 0.55, 5: 0.35}
GENOME_CAP = {"FULL": 1.0, "MEDIUM": 0.75, "LOW": 0.50}

class ConfidencePropagator:
    def propagate(self, resolved: ResolvedPrediction, 
                  genome_quality: str, 
                  breakpoint_source: str) -> Dict[str, Any]:
        """Calculate final confidence based on evidence, rules, and genome quality."""
        
        c_evidence = resolved.confidence
        ev_mod = EVIDENCE_LEVEL_MODIFIER.get(resolved.winning_rule_evidence_level, 0.5)
        
        # We simplify rule weight handling in the stub
        c_rule = 1.0 * ev_mod
        
        c_cap = GENOME_CAP.get(genome_quality, 0.50)
        
        c_final = min(c_evidence * c_rule, c_cap)
        
        tier = "HIGH" if c_final >= 0.80 else "MEDIUM" if c_final >= 0.55 else "LOW"
        
        return {
            "confidence": round(c_final, 4),
            "tier": tier,
            "cap_applied": c_final < c_evidence * c_rule
        }
