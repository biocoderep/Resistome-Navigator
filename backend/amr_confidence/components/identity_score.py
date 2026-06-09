"""Identity-based confidence component - amr_confidence v1.0.0"""

IDENTITY_THRESHOLDS = [
    (100.0, 1.000), # Perfect match
    (99.0, 0.980),
    (95.0, 0.940),
    (90.0, 0.860),
    (85.0, 0.760),
    (80.0, 0.640),
    (75.0, 0.500),
    (0.0, 0.200),
]

def identity_score(identity_pct: float) -> float:
    for threshold, score in IDENTITY_THRESHOLDS:
        if identity_pct >= threshold:
            return score
    return 0.10
