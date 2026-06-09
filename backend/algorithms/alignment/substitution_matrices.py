"""Substitution matrix loader and caching"""

from functools import lru_cache

# We embed a stub NUC4.4 matrix here to avoid file loading issues in demo
_STUB_NUC44 = {
    ('A', 'A'): 5, ('C', 'C'): 5, ('G', 'G'): 5, ('T', 'T'): 5,
    ('A', 'C'): -4, ('A', 'G'): -4, ('A', 'T'): -4,
    ('C', 'A'): -4, ('C', 'G'): -4, ('C', 'T'): -4,
    ('G', 'A'): -4, ('G', 'C'): -4, ('G', 'T'): -4,
    ('T', 'A'): -4, ('T', 'C'): -4, ('T', 'G'): -4,
}

@lru_cache(maxsize=16)
def load_matrix(name: str) -> dict:
    if name == "NUC4.4":
        return _STUB_NUC44
    return {}

def score_pair(a: str, b: str, matrix_name: str = "NUC4.4") -> int:
    matrix = load_matrix(matrix_name)
    return matrix.get((a, b), matrix.get((b, a), -4))
