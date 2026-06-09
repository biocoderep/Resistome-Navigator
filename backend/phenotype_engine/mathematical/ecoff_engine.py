"""ECOFF wild-type threshold engine - Module 1E v1.0.0"""

import math
from typing import List, Dict, Any

def compute_ecoff(log2_mic_values: List[float], method: str = "normal") -> Dict[str, Any]:
    """Compute ECOFF from log2 MIC distribution.
    Stub implementation using math instead of numpy to ensure portability."""
    
    if not log2_mic_values:
        return {}
        
    n = len(log2_mic_values)
    mu = sum(log2_mic_values) / n
    
    if n > 1:
        variance = sum((x - mu) ** 2 for x in log2_mic_values) / (n - 1)
        sigma = math.sqrt(variance)
    else:
        sigma = 0.0
        
    ecoff_log2 = mu + 3 * sigma
    ecoff_mic = 2 ** ecoff_log2
    
    return {
        "ecoff_log2": round(ecoff_log2, 3),
        "ecoff_mic": round(ecoff_mic, 3),
        "mu_log2": round(mu, 3),
        "sigma_log2": round(sigma, 3),
        "n": n,
        "method": method
    }

def classify_vs_ecoff(observed_log2_mic: float, ecoff_log2: float) -> str:
    return "non_wild_type" if observed_log2_mic > ecoff_log2 else "wild_type"
