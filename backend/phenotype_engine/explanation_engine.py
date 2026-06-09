"""Human-readable prediction explanation - Module 1E v1.0.0"""

from .result_models import PhenotypePrediction

def generate_explanation(prediction: PhenotypePrediction) -> str:
    lines = []
    lines.append(f"Predicted: {prediction.predicted_sir}")
    lines.append(f"Drug: {prediction.drug} ({prediction.drug_class})")
    lines.append(f"Confidence: {prediction.confidence_tier} ({prediction.confidence_score:.3f})")
    lines.append("")
    lines.append("Supporting Evidence:")
    
    for ev in prediction.all_candidates:
        if ev.evidence_type == "gene":
            lines.append(f"  > Gene: {ev.evidence_name}")
        elif ev.evidence_type == "mutation":
            lines.append(f"  > Mutation: {ev.evidence_name} | Evidence level: {ev.evidence_level}")
        elif ev.evidence_type == "mechanism":
            lines.append(f"  > Mechanism: {ev.evidence_name} (confidence: {ev.confidence:.3f})")
        elif ev.evidence_type == "combo":
            lines.append(f"  > Combinatorial rule matched: {ev.rule_id}")
            
    if prediction.has_conflict:
        lines.append("")
        lines.append("Note: Conflicting evidence was detected. Resistance call takes priority (R > I > S).")
        
    return "\n".join(lines)
