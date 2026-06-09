"""Bitscore normalization component - amr_confidence v1.0.0"""

from typing import Optional

def bitscore_score(bit_score: float, reference_length: int, max_expected_bitscore: Optional[float] = None) -> float:
    if max_expected_bitscore is None:
        # Theoretical max: ~2 bits per aligned base pair
        max_expected_bitscore = reference_length * 2.0
    # Avoid division by zero
    if max_expected_bitscore <= 0:
        return 0.5
    return min(bit_score / max_expected_bitscore, 1.0)
