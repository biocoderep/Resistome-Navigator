"""Needleman-Wunsch global alignment"""

__version__ = "1.0.0"

from typing import Dict, Any
from .alignment_metrics import compute_metrics
from ..utilities.result_models import AlgorithmResult

DEFAULT_PARAMS = {"match": 2, "mismatch": -3, "gap": -2}

def needleman_wunsch(query: str, reference: str, params: Dict[str, int] = DEFAULT_PARAMS) -> AlgorithmResult:
    q = query.upper()
    r = reference.upper()
    m, n = len(q), len(r)
    gap = params["gap"]
    
    F = [[0 for _ in range(n+1)] for _ in range(m+1)]
    TB = [[0 for _ in range(n+1)] for _ in range(m+1)]
    
    # Init
    for j in range(n+1):
        F[0][j] = j * gap
        TB[0][j] = 3
    for i in range(m+1):
        F[i][0] = i * gap
        TB[i][0] = 2
    TB[0][0] = 0
    
    for i in range(1, m+1):
        for j in range(1, n+1):
            s = params["match"] if q[i-1] == r[j-1] else params["mismatch"]
            diag = F[i-1][j-1] + s
            up = F[i-1][j] + gap
            left = F[i][j-1] + gap
            
            best = max(diag, up, left)
            F[i][j] = best
            
            if best == diag: TB[i][j] = 1
            elif best == up: TB[i][j] = 2
            else: TB[i][j] = 3
            
    q_aln, r_aln = _nw_traceback(TB, q, r, m, n)
    metrics = compute_metrics(q_aln, r_aln, len(r))
    
    return AlgorithmResult(
        algorithm="needleman_wunsch", 
        algorithm_version=__version__,
        inputs={"query_len": m, "ref_len": n, "params": params},
        metrics=metrics, 
        score=float(F[m][n]),
        confidence=min(metrics["identity_pct"]/100.0, 1.0),
        metadata={"q_aln": q_aln, "r_aln": r_aln}
    )

def _nw_traceback(TB: list, q: str, r: str, i: int, j: int):
    q_aln, r_aln = [], []
    while i > 0 or j > 0:
        tb = TB[i][j]
        if tb == 1:
            q_aln.append(q[i-1])
            r_aln.append(r[j-1])
            i -= 1
            j -= 1
        elif tb == 2:
            q_aln.append(q[i-1])
            r_aln.append("-")
            i -= 1
        elif tb == 3:
            q_aln.append("-")
            r_aln.append(r[j-1])
            j -= 1
    return "".join(reversed(q_aln)), "".join(reversed(r_aln))
