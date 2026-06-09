"""Explanation generator for confidence scores - amr_confidence v1.0.0"""

from .confidence_aggregation import ConfidenceResult

def explain_confidence(result: ConfidenceResult, entity_name: str) -> str:
    lines = [f"Confidence: {result.tier} ({result.overall_score:.3f})"]
    lines.append(f"Entity: {entity_name} | Context: {result.context}")
    lines.append("Component Contributions:")
    
    for comp, weighted_val in sorted(result.weighted.items(), key=lambda x: -x[1]):
        raw = result.components[comp]
        lines.append(f"  {comp:<12} raw={raw:.3f} weighted={weighted_val:.3f}")
        
    if result.cap_applied:
        lines.append("Note: Score capped by genome quality (assembly QC result).")
        
    return "\n".join(lines)
