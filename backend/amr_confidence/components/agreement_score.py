"""Database Agreement Score component - amr_confidence v1.0.0"""

from typing import List

AGREEMENT_SCORES = {
    4: 1.00, # All 4 tools agree
    3: 0.90, # 3 tools agree
    2: 0.75, # 2 tools agree
    1: 0.55, # Single tool only
}

def agreement_score(supporting_tools: List[str], max_tools: int = 4) -> float:
    n = min(len(supporting_tools), max_tools)
    return AGREEMENT_SCORES.get(n, 0.40)

def agreement_flag(supporting_tools: List[str], conflicting_tools: List[str]) -> str:
    if conflicting_tools: return "CONFLICT"
    n = len(supporting_tools)
    if n == 0: return "NO_SUPPORT"
    if n == 1: return "SINGLE_SOURCE"
    if n >= 2 and n < 4: return "PARTIAL_AGREEMENT"
    return "COMPLETE_AGREEMENT"
