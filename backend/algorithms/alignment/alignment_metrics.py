"""Alignment quality metrics"""

def compute_metrics(q_aln: str, r_aln: str, ref_length: int) -> dict:
    assert len(q_aln) == len(r_aln), "Alignment strings must be equal length"
    aln_len = len(q_aln)
    matches = sum(a == b and a != "-" for a, b in zip(q_aln, r_aln))
    mismatches = sum(a != b and a != "-" and b != "-" for a, b in zip(q_aln, r_aln))
    gaps_q = q_aln.count("-")
    gaps_r = r_aln.count("-")
    covered = sum(1 for b in r_aln if b != "-")
    
    return {
        "alignment_length": aln_len,
        "match_count": matches,
        "mismatch_count": mismatches,
        "gap_count": gaps_q + gaps_r,
        "identity_pct": round(matches / aln_len * 100, 3) if aln_len else 0.0,
        "coverage_pct": round(covered / ref_length * 100, 3) if ref_length else 0.0,
        "gap_pct": round((gaps_q+gaps_r) / aln_len * 100, 3) if aln_len else 0.0,
    }

def passes_thresholds(metrics: dict, identity_min=80.0, coverage_min=80.0) -> bool:
    return metrics["identity_pct"] >= identity_min and metrics["coverage_pct"] >= coverage_min
