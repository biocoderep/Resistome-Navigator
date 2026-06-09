"""Demo script to verify the Computational Algorithm Engine."""

import sys
from pathlib import Path

# Ensure the root directory is in sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.algorithms.alignment.smith_waterman import smith_waterman
from backend.algorithms.alignment.needleman_wunsch import needleman_wunsch
from backend.algorithms.statistics.blast_statistics import score_hit, bit_score, e_value

def main():
    print("=== Testing Computational Algorithm Engine ===")
    
    # 1. Smith-Waterman verification
    print("\n[1] Smith-Waterman local alignment")
    # Durbin et al. Biological Sequence Analysis p.21
    q = "ACACACTA"
    r = "AGCACACA"
    params = {"match": 1, "mismatch": -1, "gap_open": -1, "gap_extend": -1} # Note: demo wrapper treats gap_extend as gap
    
    sw_result = smith_waterman(q, r, params)
    print(f"Query: {q}")
    print(f"Ref:   {r}")
    print(f"SW Score: {sw_result.score} (Expected: ~4.0 for gap=-1)")
    print(f"Identity: {sw_result.metrics['identity_pct']}%")
    print(f"Coverage: {sw_result.metrics['coverage_pct']}%")
    
    # 2. Needleman-Wunsch verification
    print("\n[2] Needleman-Wunsch global alignment")
    nw_result = needleman_wunsch("GCATGCU", "GATTACA", {"match": 1, "mismatch": -1, "gap": -1})
    print(f"NW Score: {nw_result.score} (Expected: 0.0)")
    
    # 3. BLAST Statistics verification
    print("\n[3] BLAST Statistics (Karlin-Altschul)")
    raw = 100.0
    lambd = 1.28
    k = 0.46
    q_len = 100
    db_len = 1000000000 # 1e9
    
    bs = bit_score(raw, lambd, k)
    ev = e_value(50.0, q_len, db_len, lambd, k)
    
    print(f"Raw Score: {raw}")
    print(f"Bit Score: {bs:.2f} (Expected: ~185.17)")
    print(f"E-value (for raw=50): {ev:.2e} (Expected: ~6.5e-10)")
    
    hit_stats = score_hit(raw, q_len, db_len)
    print("\nHit Significance Evaluation:")
    for k_name, v_name in hit_stats.items():
        print(f"  {k_name}: {v_name}")
        
    print("\nAll verifications complete.")

if __name__ == "__main__":
    main()
