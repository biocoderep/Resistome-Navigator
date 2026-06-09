"""Coverage-based confidence component - amr_confidence v1.0.0"""

COVERAGE_THRESHOLDS = [
    (100.0, 1.000),
    (95.0, 0.960),
    (90.0, 0.900),
    (80.0, 0.800),
    (70.0, 0.680),
    (60.0, 0.550),
    (50.0, 0.400),
]

def coverage_score(coverage_pct: float, is_partial_expected: bool = False) -> float:
    base = next((s for t, s in COVERAGE_THRESHOLDS if coverage_pct >= t), 0.30)
    return min(base * 1.15, 1.0) if is_partial_expected else base
