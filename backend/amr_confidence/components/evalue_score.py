"""E-value normalization component - amr_confidence v1.0.0"""

import math

def evalue_score(e_value: float, threshold: float = 1e-5) -> float:
    if e_value <= 0:
        return 1.0
    if e_value > threshold:
        return 0.0
    log_ev = math.log10(e_value)
    log_th = math.log10(threshold)
    return max(0.0, min(1.0, 1 - log_ev / log_th))
