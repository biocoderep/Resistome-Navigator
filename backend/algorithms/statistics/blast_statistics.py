"""BLAST statistics (Karlin-Altschul) - Module 1B v1.0.0"""

__version__ = "1.0.0"

import math

# Default Karlin-Altschul parameters for nucleotide BLAST
LAMBDA_DEFAULT = 1.28
K_DEFAULT = 0.46

def bit_score(raw_score: float, lambda_: float = LAMBDA_DEFAULT, k: float = K_DEFAULT) -> float:
    """Karlin-Altschul bit score (Altschul et al. 1990)."""
    return (lambda_ * raw_score - math.log(k)) / math.log(2)

def e_value(raw_score: float, query_len: int, db_size: int, lambda_: float = LAMBDA_DEFAULT, k: float = K_DEFAULT) -> float:
    """Expected number of random hits with score >= raw_score."""
    return k * query_len * db_size * math.exp(-lambda_ * raw_score)

def score_hit(raw_score: float, query_len: int, db_size: int, e_value_threshold: float = 1e-5) -> dict:
    bs = bit_score(raw_score)
    ev = e_value(raw_score, query_len, db_size)
    
    return {
        "raw_score": raw_score,
        "bit_score": round(bs, 3),
        "e_value": ev,
        "e_value_str": f"{ev:.2e}",
        "significant": ev <= e_value_threshold,
        "confidence": max(0.0, 1.0 - min(ev, 1.0))
    }
