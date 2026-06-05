# 05 — Computational Algorithm Engine

> **Implementation Note:** This library is consumed by all other engines. No phasing — implement the full package. Priority order below.

### Implementation Priority

**Implement first (needed for MVP AMR detection and genome validation):**

| Algorithm | Module | Used By |
|-----------|--------|--------|
| Smith-Waterman | `alignment/smith_waterman.py` | AMR Detection, Mutation Detection |
| Needleman-Wunsch | `alignment/needleman_wunsch.py` | Mutation Detection |
| Alignment Metrics | `alignment/alignment_metrics.py` | All detection engines |
| Identity % | `alignment/alignment_metrics.py` | Hit classification |
| Coverage % | `alignment/alignment_metrics.py` | Hit classification |
| Bit Score | `statistics/blast_statistics.py` | Confidence scoring |
| E-value | `statistics/blast_statistics.py` | Confidence scoring |

**Implement later (Phase 2+):**

| Algorithm | Module | Phase |
|-----------|--------|-------|
| MinHash | `similarity/minhash_engine.py` | Phase 2 (duplicate detection, surveillance) |
| BWT | `search/bwt_engine.py` | Phase 2 (fast database search) |
| FM-Index | `search/fmindex_engine.py` | Phase 2 (fast pattern matching) |
| BWA-MEM | `search/bwa_mem_engine.py` | Phase 3 (mutation detection) |

---

**COMPUTATIONAL ALGORITHM ENGINE**

**SPECIFICATION**

**CAES --- Version 1.0**

**MODULE 1B --- AMR PLATFORM REUSABLE ALGORITHM LIBRARY**

*Alignment · Search · Statistics · Similarity · Indexing*

Python 3.12 · NumPy · SciPy · FastAPI · PostgreSQL

CONFIDENTIAL --- Direct Implementation Ready --- Modules 1 · 2 · 3

> **SECTION 1 --- PURPOSE AND SCOPE**

**1.1 Purpose**

The Computational Algorithm Engine (CAE) is an independently deployable, reusable Python library providing all mathematical and algorithmic primitives required by the AMR Analysis Platform. The library is consumed by Module 1 (AMR Characterisation), Module 2 (Genotype--Phenotype Concordance), and Module 3 (Mobile Genetic Element Origin Analysis) as an internal dependency --- never duplicated across modules.

**1.2 Design Principles**

  -------------------------- -----------------------------------------------------------------------------------------------------------------
  **Principle**              **Implementation**

  Modularity                 Each algorithm is a self-contained Python module importable independently; no circular dependencies

  Reusability                All algorithms accept generic sequence strings or numpy arrays; no platform-specific assumptions

  Testability                Every function has unit tests with known-answer validation from published reference results

  Performance                NumPy vectorisation used throughout; C extensions (ctypes/cffi) for inner loops where \> 10× speedup measured

  Mathematical Correctness   Each formula implemented with derivation comment and reference to source paper/textbook

  Versioning                 All algorithm modules carry \_\_version\_\_ = \"1.x.x\"; database stores algorithm_version for every result row
  -------------------------- -----------------------------------------------------------------------------------------------------------------

**1.3 Module Consumption Map**

  ---------------------- -------------------------------------------- ------------------------------- ---------------------------------
  **Algorithm Module**   **Module 1 Usage**                           **Module 2 Usage**              **Module 3 Usage**

  smith_waterman         AMR gene partial detection, virulence hits   Phenotypic MIC alignment        MGE insertion site localisation

  needleman_wunsch       Full-gene mutation calling                   Reference gene comparison       MGE boundary alignment

  blast_statistics       All AMR hit significance scoring             Concordance confidence          MGE insertion confidence

  kmer_engine            Genome validation, contamination screen      Population clustering           MGE fingerprinting

  minhash_engine         Rapid pre-screening, surveillance            Isolate similarity clustering   MGE source attribution

  bwt_engine             Database index construction                  Reference lookup                Transposon boundary search

  fmindex_engine         Fast pattern matching in AMR DB              Gene variant lookup             IS element pattern search

  similarity_engine      Cross-database result deduplication          Phenotype grouping              Plasmid family clustering

  statistics_engine      Confidence score normalisation               MIC distribution analysis       MGE prevalence stats
  ---------------------- -------------------------------------------- ------------------------------- ---------------------------------

> **SECTION 2 --- ALGORITHM FRAMEWORK ARCHITECTURE**

**2.1 Architecture Diagram**

> ┌──────────────────────────────────────────────────────────────────┐
>
> │ COMPUTATIONAL ALGORITHM ENGINE (CAE) │
>
> │ │
>
> │ ┌─────────────────────────────────────────────────────────────┐ │
>
> │ │ ALIGNMENT LAYER │ │
>
> │ │ smith_waterman.py │ needleman_wunsch.py │ │
>
> │ │ alignment_metrics.py │ substitution_matrices.py │ │
>
> │ └───────────────────────────┬─────────────────────────────────┘ │
>
> │ │ │
>
> │ ┌───────────────────────────▼─────────────────────────────────┐ │
>
> │ │ SEARCH LAYER │ │
>
> │ │ bwt_engine.py │ fmindex_engine.py │ bwa_mem_engine.py │ │
>
> │ └───────────────────────────┬─────────────────────────────────┘ │
>
> │ │ │
>
> │ ┌───────────────────────────▼─────────────────────────────────┐ │
>
> │ │ STATISTICAL LAYER │ │
>
> │ │ blast_statistics.py │ statistics_engine.py │ │
>
> │ └───────────────────────────┬─────────────────────────────────┘ │
>
> │ │ │
>
> │ ┌───────────────────────────▼─────────────────────────────────┐ │
>
> │ │ SIMILARITY LAYER │ │
>
> │ │ minhash_engine.py │ kmer_engine.py │ similarity_engine │ │
>
> │ └───────────────────────────┬─────────────────────────────────┘ │
>
> │ │ │
>
> │ ┌───────────────────────────▼─────────────────────────────────┐ │
>
> │ │ RESULT AGGREGATION LAYER │ │
>
> │ │ AlgorithmResult dataclass │ ResultSerializer │ │
>
> │ │ DB writer (db_writer.py) │ Version tagging │ │
>
> │ └─────────────────────────────────────────────────────────────┘ │
>
> └──────────────────────────────────────────────────────────────────┘

**2.2 Package Structure**

> algorithms/
>
> ├── \_\_init\_\_.py
>
> ├── alignment/
>
> │ ├── \_\_init\_\_.py
>
> │ ├── smith_waterman.py
>
> │ ├── needleman_wunsch.py
>
> │ ├── alignment_metrics.py
>
> │ └── substitution_matrices.py
>
> ├── search/
>
> │ ├── bwt_engine.py
>
> │ ├── fmindex_engine.py
>
> │ └── bwa_mem_engine.py
>
> ├── statistics/
>
> │ ├── blast_statistics.py
>
> │ └── statistics_engine.py
>
> ├── similarity/
>
> │ ├── kmer_engine.py
>
> │ ├── minhash_engine.py
>
> │ └── similarity_engine.py
>
> ├── utilities/
>
> │ ├── sequence_utils.py
>
> │ ├── db_writer.py
>
> │ └── result_models.py
>
> └── tests/
>
> ├── test_smith_waterman.py
>
> ├── test_needleman_wunsch.py
>
> ├── test_blast_statistics.py
>
> ├── test_kmer_engine.py
>
> ├── test_minhash_engine.py
>
> ├── test_bwt_engine.py
>
> ├── test_fmindex_engine.py
>
> ├── test_similarity_engine.py
>
> └── benchmarks/
>
> **SECTION 3 --- SOFTWARE DESIGN CONTRACTS**

**3.1 Standard AlgorithmResult Model**

> \# utilities/result_models.py
>
> from dataclasses import dataclass, field
>
> from typing import Any
>
> from datetime import datetime
>
> \@dataclass
>
> class AlgorithmResult:
>
> algorithm: str \# e.g. \"smith_waterman\"
>
> algorithm_version:str \# e.g. \"1.0.0\"
>
> inputs: dict \# {query_id, reference_id, parameters}
>
> metrics: dict \# algorithm-specific output metrics
>
> score: float \# primary numeric output
>
> confidence: float \# 0.0--1.0 normalised confidence
>
> executed_at: datetime = field(default_factory=datetime.utcnow)
>
> execution_ms: int = 0
>
> metadata: dict = field(default_factory=dict)

**3.2 Sequence Utilities**

> \# utilities/sequence_utils.py
>
> def complement(seq: str) -\> str:
>
> table = str.maketrans(\"ATGCatgc\", \"TACGtacg\")
>
> return seq.translate(table)
>
> def reverse_complement(seq: str) -\> str:
>
> return complement(seq)\[::-1\]
>
> def normalise(seq: str) -\> str:
>
> return seq.upper().replace(\"U\", \"T\") \# DNA normalisation
>
> **SECTION 4 --- SMITH-WATERMAN LOCAL ALIGNMENT ENGINE**

**4.1 Mathematical Foundation**

> **H(i,j) = max{ 0, H(i-1,j-1) + s(a_i, b_j), H(i-1,j) - d, H(i,j-1) - d }**

Where H(i,j) is the alignment score at position (i,j); s(a,b) is the substitution score (match reward or mismatch penalty); d is the gap extension penalty. Traceback begins at the maximum value cell and proceeds until H(i,j)=0.

**4.2 Implementation: smith_waterman.py**

> \"\"\"Smith-Waterman local alignment --- AMR Platform CAE v1.0.0\"\"\"
>
> \_\_version\_\_ = \"1.0.0\"
>
> import numpy as np
>
> from .alignment_metrics import compute_metrics
>
> from ..utilities.result_models import AlgorithmResult
>
> DEFAULT_PARAMS = {\"match\": 2, \"mismatch\": -3, \"gap_open\": -5, \"gap_extend\": -2}
>
> def smith_waterman(query: str, reference: str,
>
> params: dict = DEFAULT_PARAMS) -\> AlgorithmResult:
>
> q = query.upper(); r = reference.upper()
>
> m, n = len(q), len(r)
>
> H = np.zeros((m+1, n+1), dtype=np.int32)
>
> TB = np.zeros((m+1, n+1), dtype=np.int8) \# 0=stop,1=diag,2=up,3=left
>
> max_score, max_i, max_j = 0, 0, 0
>
> for i in range(1, m+1):
>
> for j in range(1, n+1):
>
> s = params\[\"match\"\] if q\[i-1\] == r\[j-1\] else params\[\"mismatch\"\]
>
> diag = H\[i-1,j-1\] + s
>
> up = H\[i-1,j\] + params\[\"gap_extend\"\]
>
> left = H\[i,j-1\] + params\[\"gap_extend\"\]
>
> H\[i,j\] = best = max(0, diag, up, left)
>
> TB\[i,j\] = \[0, diag, up, left\].index(best) if best \> 0 else 0
>
> if best \> max_score: max_score, max_i, max_j = best, i, j
>
> q_aln, r_aln = \_traceback(TB, q, r, max_i, max_j)
>
> metrics = compute_metrics(q_aln, r_aln, len(r))
>
> return AlgorithmResult(
>
> algorithm=\"smith_waterman\", algorithm_version=\_\_version\_\_,
>
> inputs={\"query_len\":m,\"ref_len\":n,\"params\":params},
>
> metrics=metrics, score=float(max_score),
>
> confidence=min(metrics\[\"identity_pct\"\]/100, 1.0))

**4.3 Traceback Implementation**

> def \_traceback(TB, q: str, r: str, i: int, j: int) -\> tuple\[str, str\]:
>
> q_aln, r_aln = \[\], \[\]
>
> while TB\[i,j\] != 0:
>
> tb = TB\[i,j\]
>
> if tb == 1: \# diagonal
>
> q_aln.append(q\[i-1\]); r_aln.append(r\[j-1\]); i -= 1; j -= 1
>
> elif tb == 2: \# up --- gap in reference
>
> q_aln.append(q\[i-1\]); r_aln.append(\"-\"); i -= 1
>
> else: \# left --- gap in query
>
> q_aln.append(\"-\"); r_aln.append(r\[j-1\]); j -= 1
>
> return \"\".join(reversed(q_aln)), \"\".join(reversed(r_aln))

**4.4 Vectorised NumPy Optimisation**

For sequences \> 1000 bp, the inner loop is replaced with numpy ufunc-based row-by-row computation using np.maximum.accumulate, reducing Python loop overhead by \~8× for typical AMR gene lengths (500--3000 bp).

> def \_sw_vectorised(H_prev: np.ndarray, q_char: str, r: str, params: dict) -\> np.ndarray:
>
> match_scores = np.where(np.array(list(r)) == q_char,
>
> params\[\"match\"\], params\[\"mismatch\"\])
>
> return np.maximum(0, H_prev\[:-1\] + match_scores + params\[\"gap_extend\"\])

**4.5 Unit Test Specification**

> \# tests/test_smith_waterman.py
>
> def test_identical_sequences():
>
> r = smith_waterman(\"ACGT\", \"ACGT\")
>
> assert r.metrics\[\"identity_pct\"\] == 100.0
>
> assert r.metrics\[\"coverage_pct\"\] == 100.0
>
> def test_known_answer():
>
> \# From Durbin et al. Biological Sequence Analysis p.21
>
> r = smith_waterman(\"ACACACTA\", \"AGCACACA\",
>
> {\"match\":1,\"mismatch\":-1,\"gap_open\":-1,\"gap_extend\":-1})
>
> assert r.score == 4.0
>
> **SECTION 5 --- NEEDLEMAN-WUNSCH GLOBAL ALIGNMENT ENGINE**

**5.1 Mathematical Foundation**

> **F(i,j) = max{ F(i-1,j-1) + s(a_i, b_j), F(i-1,j) - d, F(i,j-1) - d }**

Initialisation: F(i,0) = -d×i; F(0,j) = -d×j. Unlike Smith-Waterman, the matrix is never floored at zero --- the global optimum is found at F(m,n), and traceback proceeds from that cell to (0,0).

**5.2 Implementation: needleman_wunsch.py**

> \"\"\"Needleman-Wunsch global alignment --- AMR Platform CAE v1.0.0\"\"\"
>
> \_\_version\_\_ = \"1.0.0\"
>
> import numpy as np
>
> def needleman_wunsch(query: str, reference: str,
>
> match=2, mismatch=-3, gap=-2) -\> AlgorithmResult:
>
> q = query.upper(); r = reference.upper()
>
> m, n = len(q), len(r)
>
> F = np.zeros((m+1, n+1), dtype=np.float32)
>
> TB = np.zeros((m+1, n+1), dtype=np.int8)
>
> \# Initialisation with gap penalties
>
> F\[0, :\] = np.arange(n+1) \* gap
>
> F\[:, 0\] = np.arange(m+1) \* gap
>
> TB\[0, 1:\] = 3 \# left
>
> TB\[1:, 0\] = 2 \# up
>
> \# Fill
>
> for i in range(1, m+1):
>
> for j in range(1, n+1):
>
> s = match if q\[i-1\] == r\[j-1\] else mismatch
>
> scores = \[F\[i-1,j-1\]+s, F\[i-1,j\]+gap, F\[i,j-1\]+gap\]
>
> best_idx = int(np.argmax(scores))
>
> F\[i,j\] = scores\[best_idx\]
>
> TB\[i,j\] = best_idx + 1 \# 1=diag, 2=up, 3=left
>
> q_aln, r_aln = \_nw_traceback(TB, q, r, m, n)
>
> metrics = compute_metrics(q_aln, r_aln, len(r))
>
> return AlgorithmResult(\"needleman_wunsch\", \_\_version\_\_, {}, metrics, F\[m,n\], \...)
>
> **SECTION 6 --- ALIGNMENT METRICS ENGINE**

**6.1 Metric Formulae**

> **% Identity = (Matches / Alignment_Length) × 100**
>
> **% Coverage = (Aligned_Reference_Bases / Reference_Length) × 100**
>
> **% Gaps = (Gap_Characters / Alignment_Length) × 100**

**6.2 Implementation: alignment_metrics.py**

> \"\"\"Alignment quality metrics --- AMR Platform CAE v1.0.0\"\"\"
>
> def compute_metrics(q_aln: str, r_aln: str, ref_length: int) -\> dict:
>
> assert len(q_aln) == len(r_aln), \"Alignment strings must be equal length\"
>
> aln_len = len(q_aln)
>
> matches = sum(a == b and a != \"-\" for a, b in zip(q_aln, r_aln))
>
> mismatches= sum(a != b and a != \"-\" and b != \"-\" for a, b in zip(q_aln, r_aln))
>
> gaps_q = q_aln.count(\"-\")
>
> gaps_r = r_aln.count(\"-\")
>
> covered = sum(1 for b in r_aln if b != \"-\")
>
> return {
>
> \"alignment_length\": aln_len,
>
> \"match_count\": matches,
>
> \"mismatch_count\": mismatches,
>
> \"gap_count\": gaps_q + gaps_r,
>
> \"identity_pct\": round(matches / aln_len \* 100, 3) if aln_len else 0.0,
>
> \"coverage_pct\": round(covered / ref_length \* 100, 3) if ref_length else 0.0,
>
> \"gap_pct\": round((gaps_q+gaps_r) / aln_len \* 100, 3) if aln_len else 0.0,
>
> }
>
> def passes_thresholds(metrics: dict, identity_min=80.0, coverage_min=80.0) -\> bool:
>
> return metrics\[\"identity_pct\"\] \>= identity_min and metrics\[\"coverage_pct\"\] \>= coverage_min
>
> **SECTION 7 --- BLAST STATISTICS ENGINE**

**7.1 Mathematical Foundation**

> **Bit Score: S\' = (λ × S − ln K) / ln 2**
>
> **E-value: E = K × m × n × e\^(−λ × S)**

Where S = raw alignment score, λ = Karlin-Altschul statistical parameter (default 1.28 for nucleotide BLAST), K = statistical constant (default 0.46), m = query length (bp), n = effective database size (bp). E-value \< 1×10⁻⁵ is the default reporting threshold for AMR gene hits.

**7.2 Implementation: blast_statistics.py**

> \"\"\"BLAST statistics (Karlin-Altschul) --- AMR Platform CAE v1.0.0\"\"\"
>
> \_\_version\_\_ = \"1.0.0\"
>
> import math
>
> \# Default Karlin-Altschul parameters for nucleotide BLAST
>
> LAMBDA_DEFAULT = 1.28
>
> K_DEFAULT = 0.46
>
> def bit_score(raw_score: float,
>
> lambda\_: float = LAMBDA_DEFAULT,
>
> k: float = K_DEFAULT) -\> float:
>
> \"\"\"Karlin-Altschul bit score (Altschul et al. 1990).\"\"\"
>
> return (lambda\_ \* raw_score - math.log(k)) / math.log(2)
>
> def e_value(raw_score: float, query_len: int, db_size: int,
>
> lambda\_: float = LAMBDA_DEFAULT, k: float = K_DEFAULT) -\> float:
>
> \"\"\"Expected number of random hits with score \>= raw_score.\"\"\"
>
> return k \* query_len \* db_size \* math.exp(-lambda\_ \* raw_score)
>
> def score_hit(raw_score: float, query_len: int, db_size: int,
>
> e_value_threshold: float = 1e-5) -\> dict:
>
> bs = bit_score(raw_score)
>
> ev = e_value(raw_score, query_len, db_size)
>
> return {
>
> \"raw_score\": raw_score,
>
> \"bit_score\": round(bs, 3),
>
> \"e_value\": ev,
>
> \"e_value_str\": f\"{ev:.2e}\",
>
> \"significant\": ev \<= e_value_threshold,
>
> \"confidence\": max(0.0, 1.0 - min(ev, 1.0))}
>
> **SECTION 8 --- SUBSTITUTION MATRIX ENGINE**

**8.1 Supported Matrices**

  -------------- ------------ ----------------------------------------- ----------------------
  **Matrix**     **Type**     **Best For**                              **Gap Open Penalty**

  BLOSUM62       Protein      General AMR protein alignment (default)   -11

  BLOSUM80       Protein      High-identity hits (\> 80% identity)      -10

  BLOSUM45       Protein      Distant homology (\< 40% identity)        -13

  PAM30          Protein      Very close homology (\< 1% divergence)    -9

  PAM70          Protein      Close homology (\< 5% divergence)         -10

  PAM250         Protein      Distant homology                          -14

  NUC4.4         Nucleotide   Standard nucleotide BLAST scoring         -5
  -------------- ------------ ----------------------------------------- ----------------------

**8.2 Implementation: substitution_matrices.py**

> \"\"\"Substitution matrix loader and caching --- AMR Platform CAE v1.0.0\"\"\"
>
> from functools import lru_cache
>
> from pathlib import Path
>
> import json
>
> \_MATRIX_DIR = Path(\_\_file\_\_).parent / \"data\" / \"matrices\"
>
> \@lru_cache(maxsize=16)
>
> def load_matrix(name: str) -\> dict\[tuple, int\]:
>
> \"\"\"Load and cache substitution matrix. Name: BLOSUM62, PAM30, NUC4.4, etc.\"\"\"
>
> path = \_MATRIX_DIR / f\"{name.upper()}.json\"
>
> if not path.exists():
>
> raise ValueError(f\"Unknown matrix: {name}. Available: {list_matrices()}\")
>
> data = json.loads(path.read_text())
>
> return {(a, b): v for (a, b), v in data.items()}
>
> def score_pair(a: str, b: str, matrix_name: str = \"BLOSUM62\") -\> int:
>
> matrix = load_matrix(matrix_name)
>
> return matrix.get((a, b), matrix.get((b, a), -4)) \# symmetric lookup
>
> **SECTION 9 --- K-MER ENGINE**

**9.1 Purpose and Applications**

  ------------- -------------------------------------------------- ------------------ ------------------
  **k value**   **Use Case**                                       **Specificity**    **Sensitivity**

  k=15          Quick contamination screen                         Low                High

  k=21          Standard genome comparison, species prediction     Medium             High

  k=31          AMR gene fingerprinting, contamination detection   High               Medium

  k=51          Strain-level discrimination                        Very High          Lower
  ------------- -------------------------------------------------- ------------------ ------------------

**9.2 Implementation: kmer_engine.py**

> \"\"\"K-mer analysis engine --- AMR Platform CAE v1.0.0\"\"\"
>
> \_\_version\_\_ = \"1.0.0\"
>
> from collections import Counter
>
> import numpy as np
>
> def build_kmer_profile(sequences: list\[str\], k: int,
>
> skip_n: bool = True) -\> dict\[str, int\]:
>
> \"\"\"Build k-mer frequency profile from list of sequences.\"\"\"
>
> counter = Counter()
>
> for seq in sequences:
>
> s = seq.upper()
>
> for i in range(len(s) - k + 1):
>
> kmer = s\[i:i+k\]
>
> if skip_n and \"N\" in kmer: continue
>
> counter\[kmer\] += 1
>
> return dict(counter)
>
> def kmer_statistics(profile: dict) -\> dict:
>
> freqs = np.array(list(profile.values()), dtype=np.int64)
>
> total = int(freqs.sum())
>
> return {
>
> \"total_kmers\": total,
>
> \"unique_kmers\": len(freqs),
>
> \"singleton_count\": int((freqs == 1).sum()),
>
> \"singleton_pct\": round((freqs == 1).sum() / len(freqs) \* 100, 2),
>
> \"max_frequency\": int(freqs.max()),
>
> \"mean_frequency\": round(float(freqs.mean()), 3),
>
> \"coverage_estimate\": round(float(freqs.mean()), 2)
>
> }
>
> def compare_kmer_profiles(profile_a: dict, profile_b: dict) -\> float:
>
> \"\"\"Jaccard similarity between two k-mer sets (ignores frequency).\"\"\"
>
> set_a, set_b = set(profile_a), set(profile_b)
>
> return len(set_a & set_b) / len(set_a \| set_b) if set_a \| set_b else 0.0
>
> **SECTION 10 --- MINHASH ENGINE**

**10.1 Mathematical Foundation**

> **J(A, B) = \|A ∩ B\| / \|A ∪ B\| (Jaccard Similarity)**

MinHash approximates Jaccard similarity in O(n) time and O(s) space where s = sketch size (number of hash permutations), regardless of genome size. Probability that min-hash(A) = min-hash(B) for a given permutation equals J(A,B).

**10.2 Implementation: minhash_engine.py**

> \"\"\"MinHash similarity engine --- AMR Platform CAE v1.0.0\"\"\"
>
> \_\_version\_\_ = \"1.0.0\"
>
> from datasketch import MinHash, MinHashLSH
>
> import pickle
>
> DEFAULT_NUM_PERM = 128 \# 128 permutations ≈ ±5% Jaccard error
>
> DEFAULT_K = 21
>
> def build_minhash(sequence: str,
>
> k: int = DEFAULT_K,
>
> num_perm: int = DEFAULT_NUM_PERM) -\> MinHash:
>
> \"\"\"Build MinHash sketch from a DNA sequence.\"\"\"
>
> mh = MinHash(num_perm=num_perm)
>
> seq = sequence.upper()
>
> for i in range(len(seq) - k + 1):
>
> kmer = seq\[i:i+k\]
>
> if \"N\" not in kmer:
>
> mh.update(kmer.encode(\"utf-8\"))
>
> return mh
>
> def jaccard_similarity(mh_a: MinHash, mh_b: MinHash) -\> float:
>
> return mh_a.jaccard(mh_b)
>
> def build_lsh_index(sketches: list\[tuple\[str, MinHash\]\],
>
> threshold: float = 0.5,
>
> num_perm: int = DEFAULT_NUM_PERM) -\> MinHashLSH:
>
> \"\"\"Build LSH index for sub-linear similarity search.\"\"\"
>
> lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
>
> for name, mh in sketches:
>
> lsh.insert(name, mh)
>
> return lsh
>
> def query_lsh(lsh: MinHashLSH, query_mh: MinHash) -\> list\[str\]:
>
> \"\"\"Return candidate similar sequences above LSH threshold.\"\"\"
>
> return lsh.query(query_mh)

**10.3 Genome-Level Comparison**

> def genome_similarity(seqs_a: list\[str\], seqs_b: list\[str\],
>
> k: int = 21, num_perm: int = 128) -\> float:
>
> \"\"\"MinHash Jaccard similarity between two genomes (concatenate contigs).\"\"\"
>
> mh_a = build_minhash(\"\".join(seqs_a), k, num_perm)
>
> mh_b = build_minhash(\"\".join(seqs_b), k, num_perm)
>
> return jaccard_similarity(mh_a, mh_b)
>
> **SECTION 11 --- BURROWS-WHEELER TRANSFORM ENGINE**

**11.1 Mathematical Foundation**

The BWT rearranges a string S of length n into a form that compresses better and enables efficient pattern searching. Given S with appended sentinel \"\$\" (lexicographically smallest character), the BWT(S) = last column of the sorted matrix of all cyclic rotations of S.

> **BWT(S) = S\[SA\[i\] - 1\] for each suffix array position SA\[i\]**

**11.2 Implementation: bwt_engine.py**

> \"\"\"Burrows-Wheeler Transform --- AMR Platform CAE v1.0.0\"\"\"
>
> \_\_version\_\_ = \"1.0.0\"
>
> def build_bwt(text: str) -\> tuple\[str, list\[int\]\]:
>
> \"\"\"Build BWT and suffix array for text. Appends sentinel \$.\"\"\"
>
> s = text + \"\$\"
>
> n = len(s)
>
> \# Build suffix array via sorted suffixes (O(n log n) for this implementation)
>
> sa = sorted(range(n), key=lambda i: s\[i:\])
>
> bwt = \"\".join(s\[i-1\] for i in sa)
>
> return bwt, sa
>
> def inverse_bwt(bwt: str) -\> str:
>
> \"\"\"Reconstruct original string from BWT.\"\"\"
>
> n = len(bwt)
>
> \# LF-mapping: sort BWT to get F column, track indices
>
> table = sorted((char, i) for i, char in enumerate(bwt))
>
> \# Reconstruct by following LF-mapping from \$ position
>
> row = next(i for i, (c, \_) in enumerate(table) if c == \"\$\")
>
> result = \[\]
>
> for \_ in range(n - 1):
>
> char, orig = table\[row\]
>
> result.append(char)
>
> row = orig
>
> return \"\".join(reversed(result))
>
> def bwt_count_occurrences(bwt: str, pattern: str) -\> int:
>
> \"\"\"Count exact occurrences of pattern using BWT rank queries.\"\"\"
>
> from .fmindex_engine import FMIndex
>
> return FMIndex(bwt).count(pattern)
>
> **SECTION 12 --- FM-INDEX ENGINE**

**12.1 Algorithm Overview**

The FM-Index combines the BWT with a rank/select data structure to enable backward search for pattern P in O(\|P\|) time after O(n) preprocessing. The backward search algorithm narrows the suffix array interval \[lo, hi) for each character of P from right to left.

> **Backward search: lo = C\[c\] + Occ(c, lo-1) + 1; hi = C\[c\] + Occ(c, hi)**

Where C\[c\] = number of characters lexicographically smaller than c; Occ(c, i) = occurrences of c in BWT\[0..i\].

**12.2 Implementation: fmindex_engine.py**

> \"\"\"FM-Index for compressed pattern matching --- AMR Platform CAE v1.0.0\"\"\"
>
> \_\_version\_\_ = \"1.0.0\"
>
> from collections import defaultdict
>
> class FMIndex:
>
> def \_\_init\_\_(self, text: str):
>
> from .bwt_engine import build_bwt
>
> self.bwt, self.sa = build_bwt(text)
>
> self.n = len(self.bwt)
>
> self.\_build_occ(); self.\_build_c()
>
> def \_build_occ(self):
>
> \"\"\"Occ\[c\]\[i\] = occurrences of c in BWT\[0..i-1\].\"\"\"
>
> self.occ = defaultdict(lambda: \[0\] \* (self.n + 1))
>
> for i, c in enumerate(self.bwt):
>
> for ch in self.occ: self.occ\[ch\]\[i+1\] = self.occ\[ch\]\[i\]
>
> self.occ\[c\]\[i+1\] = self.occ\[c\]\[i\] + 1
>
> def \_build_c(self):
>
> \"\"\"C\[c\] = number of characters \< c in original string.\"\"\"
>
> freq = defaultdict(int)
>
> for c in self.bwt: freq\[c\] += 1
>
> self.c = {}
>
> total = 0
>
> for ch in sorted(freq):
>
> self.c\[ch\] = total
>
> total += freq\[ch\]
>
> def count(self, pattern: str) -\> int:
>
> \"\"\"Count occurrences of pattern using backward search.\"\"\"
>
> lo, hi = 0, self.n
>
> for char in reversed(pattern):
>
> if char not in self.c: return 0
>
> lo = self.c\[char\] + self.occ\[char\]\[lo\]
>
> hi = self.c\[char\] + self.occ\[char\]\[hi\]
>
> if lo \>= hi: return 0
>
> return hi - lo
>
> def locate(self, pattern: str) -\> list\[int\]:
>
> \"\"\"Return sorted list of all occurrence positions of pattern.\"\"\"
>
> lo, hi = 0, self.n
>
> for char in reversed(pattern):
>
> if char not in self.c: return \[\]
>
> lo = self.c\[char\] + self.occ\[char\]\[lo\]
>
> hi = self.c\[char\] + self.occ\[char\]\[hi\]
>
> return sorted(self.sa\[i\] for i in range(lo, hi))
>
> **SECTION 13 --- BWA-MEM CONCEPTUAL ENGINE**

**13.1 Algorithm Concept**

BWA-MEM (Li 2013) chains super-maximal exact matches (SMEMs) seeded from the FM-Index, then extends chains with Smith-Waterman. This module provides the conceptual pipeline reusing the platform\'s own FM-Index and Smith-Waterman modules --- it is a wrapper layer, not a reimplementation of the full BWA-MEM tool.

**13.2 Implementation: bwa_mem_engine.py**

> \"\"\"BWA-MEM conceptual alignment engine --- AMR Platform CAE v1.0.0\"\"\"
>
> \_\_version\_\_ = \"1.0.0\"
>
> from .fmindex_engine import FMIndex
>
> from ..alignment.smith_waterman import smith_waterman
>
> class BWAMemEngine:
>
> def \_\_init\_\_(self, reference: str):
>
> self.reference = reference.upper()
>
> self.index = FMIndex(self.reference)
>
> def find_mems(self, query: str, min_len: int = 19) -\> list\[dict\]:
>
> \"\"\"Find super-maximal exact matches (SMEMs) of query in reference.\"\"\"
>
> q = query.upper()
>
> mems = \[\]
>
> for i in range(len(q)):
>
> \# Extend rightward from position i
>
> for j in range(i + min_len, len(q) + 1):
>
> seed = q\[i:j\]
>
> count = self.index.count(seed)
>
> if count == 0:
>
> \# Broke uniqueness: record previous (i, j-1) as MEM
>
> if j - 1 - i \>= min_len:
>
> positions = self.index.locate(q\[i:j-1\])
>
> mems.append({\"q_start\":i, \"q_end\":j-1,
>
> \"ref_positions\":positions, \"length\":j-1-i})
>
> break
>
> return mems
>
> def align(self, query: str, min_mem: int = 19,
>
> sw_identity_threshold: float = 0.80) -\> dict:
>
> \"\"\"Seed-and-extend alignment of query against reference.\"\"\"
>
> mems = self.find_mems(query, min_mem)
>
> if not mems:
>
> return {\"status\": \"NO_SEEDS\", \"mems\": \[\], \"alignment\": None}
>
> \# Extend best seed with Smith-Waterman
>
> best_mem = max(mems, key=lambda m: m\[\"length\"\])
>
> ref_start = best_mem\[\"ref_positions\"\]\[0\]
>
> window_start = max(0, ref_start - len(query)//2)
>
> window_end = min(len(self.reference), ref_start + len(query) \* 2)
>
> ref_window = self.reference\[window_start:window_end\]
>
> aln = smith_waterman(query, ref_window)
>
> return {\"status\":\"ALIGNED\",\"mems\":mems,\"alignment\":aln,\"ref_window_start\":window_start}
>
> **SECTION 14 --- SIMILARITY ENGINE**

**14.1 Similarity Metrics**

  --------------- ------------------------------------------ --------------------- ----------------------------------------------------
  **Metric**      **Formula**                                **Range**             **Use Case**

  Jaccard         \|A ∩ B\| / \|A ∪ B\|                      0--1                  K-mer set overlap; gene content similarity

  Cosine          A·B / (\|A\| × \|B\|)                      0--1                  K-mer frequency vector similarity; abundance-aware

  Hamming         Count of positions where A\[i\] ≠ B\[i\]   0--n                  Bitwise distance for equal-length sequences

  Edit Distance   Min insert/delete/substitute ops           0--max(\|A\|,\|B\|)   Sequence divergence for short sequences

  Mash Distance   d = -1/k × ln(2J/(1+J))                    0--1                  Genomic distance approximation from k-mers
  --------------- ------------------------------------------ --------------------- ----------------------------------------------------

**14.2 Implementation: similarity_engine.py**

> \"\"\"Sequence similarity metrics --- AMR Platform CAE v1.0.0\"\"\"
>
> \_\_version\_\_ = \"1.0.0\"
>
> import numpy as np
>
> def jaccard(set_a: set, set_b: set) -\> float:
>
> union = set_a \| set_b
>
> return len(set_a & set_b) / len(union) if union else 0.0
>
> def cosine(vec_a: dict, vec_b: dict) -\> float:
>
> keys = set(vec_a) \| set(vec_b)
>
> a = np.array(\[vec_a.get(k, 0) for k in keys\], dtype=float)
>
> b = np.array(\[vec_b.get(k, 0) for k in keys\], dtype=float)
>
> denom = np.linalg.norm(a) \* np.linalg.norm(b)
>
> return float(np.dot(a, b) / denom) if denom else 0.0
>
> def mash_distance(jaccard_sim: float, k: int = 21) -\> float:
>
> \"\"\"Convert Jaccard similarity to Mash genomic distance.\"\"\"
>
> import math
>
> j = max(jaccard_sim, 1e-9) \# avoid log(0)
>
> return -1/k \* math.log(2\*j / (1+j))
>
> def edit_distance(s: str, t: str) -\> int:
>
> \"\"\"Classic Levenshtein edit distance (DP).\"\"\"
>
> m, n = len(s), len(t)
>
> dp = np.arange(n + 1, dtype=np.int32)
>
> for i in range(1, m + 1):
>
> prev, dp\[0\] = dp\[0\], i
>
> for j in range(1, n + 1):
>
> prev, dp\[j\] = dp\[j\], min(prev+(s\[i-1\]!=t\[j-1\]), dp\[j\]+1, dp\[j-1\]+1)
>
> return int(dp\[n\])
>
> **SECTION 15 --- STATISTICAL ANALYSIS ENGINE**

**15.1 Metrics Implemented**

> **Z-score: z = (x − μ) / σ**
>
> **95% CI: x̄ ± 1.96 × (σ / √n)**

**15.2 Implementation: statistics_engine.py**

> \"\"\"Statistical analysis engine --- AMR Platform CAE v1.0.0\"\"\"
>
> \_\_version\_\_ = \"1.0.0\"
>
> import numpy as np
>
> from scipy import stats
>
> def describe(values: list\[float\]) -\> dict:
>
> a = np.array(values, dtype=np.float64)
>
> n = len(a)
>
> mean = float(np.mean(a))
>
> std = float(np.std(a, ddof=1)) if n \> 1 else 0.0
>
> return {
>
> \"n\": n,
>
> \"mean\": round(mean, 6),
>
> \"median\": round(float(np.median(a)), 6),
>
> \"std\": round(std, 6),
>
> \"variance\": round(float(np.var(a, ddof=1)), 6) if n \> 1 else 0.0,
>
> \"min\": float(a.min()),
>
> \"max\": float(a.max()),
>
> \"p25\": float(np.percentile(a, 25)),
>
> \"p75\": float(np.percentile(a, 75)),
>
> \"p95\": float(np.percentile(a, 95)),
>
> }
>
> def z_scores(values: list\[float\]) -\> list\[float\]:
>
> a = np.array(values, dtype=np.float64)
>
> return list(stats.zscore(a, ddof=1))
>
> def confidence_interval(values: list\[float\], ci: float = 0.95) -\> tuple\[float, float\]:
>
> a = np.array(values, dtype=np.float64)
>
> return tuple(stats.t.interval(ci, len(a)-1, loc=np.mean(a), scale=stats.sem(a)))
>
> def normalise_score(raw: float, min_val: float, max_val: float) -\> float:
>
> \"\"\"Linear normalisation to \[0, 1\].\"\"\"
>
> if max_val == min_val: return 0.0
>
> return max(0.0, min(1.0, (raw - min_val) / (max_val - min_val)))
>
> **SECTION 16 --- PERFORMANCE OPTIMISATION**

**16.1 Optimisation Strategy**

  --------------------- -------------------------------------------------------------------- ---------------------- ---------------------------------------------------------------------------
  **Technique**         **Applied To**                                                       **Expected Speedup**   **Implementation**

  NumPy vectorisation   SW/NW fill row-by-row, k-mer counting, stat functions                5--10×                 Replace Python for-loops with np.maximum, np.where, Counter → np.bincount

  LRU caching           Substitution matrix loads, FM-Index builds for repeated references   100× on repeat calls   \@functools.lru_cache on load_matrix(); FMIndex cached by reference hash

  Chunked processing    K-mer profiles for large genomes (\> 10 Mb)                          Constant memory        Process 1 MB chunks; merge Counters

  Multiprocessing       Batch alignment (process pool per contig)                            N_CPU ×                concurrent.futures.ProcessPoolExecutor for independent alignments

  C extension           SW inner loop for sequences \> 5 kbp                                 15--30×                libssw via ctypes for production; Python fallback always present

  Memory mapping        Large reference FASTA for FM-Index construction                      Reduced RAM            mmap.mmap for reference sequences \> 100 MB

  GPU (future)          Batch SW for large surveillance screens                              100×+                  CuPy drop-in for numpy arrays; CUDA kernel via numba for DP matrix
  --------------------- -------------------------------------------------------------------- ---------------------- ---------------------------------------------------------------------------

**16.2 Benchmark Targets**

  ------------------------------ -------------------------- ----------------------- --------------------------
  **Operation**                  **Input Size**             **Target Throughput**   **Measurement Method**

  Smith-Waterman                 500 bp query × 1 kbp ref   \< 5 ms                 pytest-benchmark median

  Smith-Waterman (vectorised)    3 kbp query × 3 kbp ref    \< 50 ms                pytest-benchmark median

  K-mer profile build (k=21)     5 Mb genome                \< 2 seconds            time.perf_counter

  MinHash sketch                 5 Mb genome                \< 3 seconds            time.perf_counter

  FM-Index build                 5 Mb reference             \< 10 seconds           time.perf_counter

  FM-Index query                 21-bp pattern              \< 1 ms                 pytest-benchmark median

  Jaccard similarity (MinHash)   2 × 5 Mb genomes           \< 100 ms               includes sketch build
  ------------------------------ -------------------------- ----------------------- --------------------------

> **SECTION 17 --- DATABASE INTEGRATION**

**17.1 Table Mappings**

  -------------------------- -------------------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Algorithm Output**       **Table**                  **Key Columns**

  SW / NW alignment result   alignment_results          sample_id, search_method, query_sequence, reference_name, alignment_score, identity_pct, coverage_pct, query_start, query_end, ref_start, ref_end, cigar_string

  BLAST statistics           blast_statistics           alignment_id (FK), bit_score, e_value, raw_score, gap_opens, mismatch_count, match_count, db_size_bases

  K-mer profile              search_metrics             sample_id, search_method=\"kmer\", metric_name, metric_value (JSONB)

  MinHash similarity pair    similarity_metrics (new)   sample_id_a, sample_id_b, method=\"minhash\", jaccard_similarity, k, num_perm, computed_at

  Statistics summary         embedded JSONB             Stored in amr_genes.confidence_components as JSONB; no separate table
  -------------------------- -------------------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------

**17.2 New Table: similarity_metrics**

> CREATE TABLE similarity_metrics (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> sample_id_a UUID NOT NULL REFERENCES samples(id) ON DELETE CASCADE,
>
> sample_id_b UUID NOT NULL REFERENCES samples(id) ON DELETE CASCADE,
>
> method VARCHAR(50) NOT NULL, \-- minhash \| kmer_jaccard \| cosine
>
> similarity NUMERIC(8,6) NOT NULL, \-- 0.0--1.0
>
> distance NUMERIC(8,6), \-- derived (e.g. Mash distance)
>
> k SMALLINT,
>
> parameters JSONB, \-- {num_perm:128}
>
> algorithm_version VARCHAR(20),
>
> computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
>
> CONSTRAINT uq_sim UNIQUE (sample_id_a, sample_id_b, method, k)
>
> CREATE INDEX idx_sim_a ON similarity_metrics (sample_id_a);
>
> CREATE INDEX idx_sim_b ON similarity_metrics (sample_id_b);
>
> **SECTION 18 --- FASTAPI SERVICE DESIGN**

**18.1 Endpoints**

  ------------ ------------------------------------ ------------------------------------------------------------- -----------------------------------------
  **Method**   **Path**                             **Description**                                               **Async**

  POST         /api/v1/algorithms/alignment         Run SW or NW alignment; returns alignment result + metrics    No (sync, fast)

  POST         /api/v1/algorithms/blast             Compute BLAST statistics for a raw alignment score            No (sync)

  POST         /api/v1/algorithms/minhash           Build MinHash sketch for a sequence set; returns sketch ID    No (sync)

  POST         /api/v1/algorithms/minhash/compare   Compare two sketches (by ID or inline) → Jaccard similarity   No (sync)

  POST         /api/v1/algorithms/kmer              Build k-mer profile for sequence list → statistics            No (sync \< 5 Mb) / Yes (async \> 5 Mb)

  POST         /api/v1/algorithms/search            FM-Index pattern search against an indexed reference          Yes (index build is async)

  GET          /api/v1/algorithms/results/{id}      Retrieve stored algorithm result by UUID                      No
  ------------ ------------------------------------ ------------------------------------------------------------- -----------------------------------------

**18.2 Alignment Endpoint --- Request / Response**

> \# Request
>
> {
>
> \"query\": \"ATGCGTACGATCGATCGTAGCATCGT\", // required, ≤ 100 kbp
>
> \"reference\": \"GCGTACGATCGATCGTAGCATCGTATC\", // required, ≤ 100 kbp
>
> \"method\": \"smith_waterman\", // smith_waterman \| needleman_wunsch
>
> \"params\": {\"match\":2,\"mismatch\":-3,\"gap_open\":-5,\"gap_extend\":-2},
>
> \"matrix\": \"NUC4.4\", // optional substitution matrix name
>
> \"store_result\": true // persist to alignment_results table
>
> \# Response 200
>
> {
>
> \"status\": \"success\",
>
> \"data\": {
>
> \"result_id\": \"uuid\",
>
> \"method\": \"smith_waterman\",
>
> \"score\": 48.0,
>
> \"identity_pct\": 92.3,
>
> \"coverage_pct\": 100.0,
>
> \"alignment_length\":26,
>
> \"match_count\": 24,
>
> \"mismatch_count\": 2,
>
> \"gap_count\": 0,
>
> \"q_aligned\": \"ATGCGTACGATCGATCGTAGCATCGT\",
>
> \"r_aligned\": \"GCGTACGATCGATCGTAGCATCGTATC\",
>
> \"execution_ms\": 3
>
> **SECTION 19 --- TESTING STRATEGY**

**19.1 Test Categories**

  ------------------------- ----------------------------------------------- --------------------------------------------------------------------------------- ------------------------------------------------------------------------------------------------------------
  **Category**              **Framework**                                   **Scope**                                                                         **Key Assertions**

  Mathematical Validation   pytest + known-answer fixtures                  Every formula verified against published reference results or textbook examples   SW score matches Durbin et al.; NW score matches NCBI BLAST; bit_score matches BLAST result for known pair

  Unit Tests                pytest                                          Individual functions; edge cases (empty seq, identical seq, all-N seq)            ≥ 95% line coverage; 100% on core alignment functions

  Integration Tests         pytest + testcontainers                         End-to-end API call → DB write → result retrieval                                 Alignment result stored and retrievable; confidence score correct

  Performance Benchmarks    pytest-benchmark                                Timing of each algorithm at defined input sizes                                   All benchmarks within defined targets (Section 16.2)

  Regression Tests          pytest fixtures with pinned version snapshots   Output stability across code versions                                             Results for 10 reference sequence pairs identical ± 1e-6 across versions

  Load Tests                locust                                          100 concurrent alignment requests                                                 \< 200ms p95; zero 5xx errors
  ------------------------- ----------------------------------------------- --------------------------------------------------------------------------------- ------------------------------------------------------------------------------------------------------------

**19.2 Reference Test Cases**

  ----------------- ------------------------------------------------------ ------------------------------ --------------------------
  **Test**          **Input**                                              **Expected Output**            **Source**

  SW identical      query=ref=\"ACGT\", match=2, gap=-2                    score=8, identity=100%         Trivial

  SW known          ACACACTA vs AGCACACA, match=1, mismatch=-1, gap=-1     score=4.0                      Durbin et al. p.21

  NW full gap       GCATGCU vs GATTACA, match=1, mismatch=-1, gap=-1       score=0.0                      Wikipedia NW article

  Bit score         raw_score=100, lambda=1.28, K=0.46                     185.17                         BLAST manual calculation

  E-value           raw_score=50, query=100, db=1e9, lambda=1.28, K=0.46   \~6.5e-10                      BLAST manual calculation

  MinHash Jaccard   Identical sequences                                    1.0                            Trivial

  K-mer profile     \"ACGT\" k=2                                           {\"AC\":1,\"CG\":1,\"GT\":1}   Manual
  ----------------- ------------------------------------------------------ ------------------------------ --------------------------

> **SECTION 20 --- DOCUMENTATION REQUIREMENTS**

**20.1 Documentation Standards**

  --------------------------- ------------------------------------------------------------------------ -------------------- ----------------------------------
  **Documentation Type**      **Standard**                                                             **Tool**             **Location**

  Mathematical derivation     Formula as block comment above each function with reference citation     In-code comments     Every formula function

  Docstrings                  Google-style docstrings: Args, Returns, Raises, Example                  pdoc3 / MkDocs       All public functions and classes

  Biological interpretation   Markdown explanation of when to use each algorithm in AMR context        MkDocs site          docs/algorithms/

  API documentation           OpenAPI 3.1 auto-generated via FastAPI                                   Swagger UI / Redoc   /api/v1/docs

  Developer guide             How to add a new algorithm module; test conventions; versioning policy   MkDocs               docs/developer/

  Changelog                   CHANGELOG.md following keepachangelog.com format                         Manual + git-cliff   Root of repository
  --------------------------- ------------------------------------------------------------------------ -------------------- ----------------------------------

**20.2 Docstring Template**

> def smith_waterman(query: str, reference: str, params: dict) -\> AlgorithmResult:
>
> \"\"\"Local sequence alignment using Smith-Waterman dynamic programming.
>
> Implements: H(i,j) = max{0, H(i-1,j-1)+s(a,b), H(i-1,j)-d, H(i,j-1)-d}
>
> Reference: Smith & Waterman (1981) J. Mol. Biol. 147:195-197
>
> Biological interpretation: Identifies locally homologous regions between
>
> query and reference; optimal for detecting partial AMR gene hits where only
>
> a sub-region of the gene is present in the assembly.
>
> Args:
>
> query: Query sequence (nucleotide or protein, uppercase or lower)
>
> reference: Reference sequence
>
> params: Scoring parameters dict with keys: match, mismatch,
>
> gap_open, gap_extend
>
> Returns:
>
> AlgorithmResult with metrics: identity_pct, coverage_pct,
>
> alignment_length, match_count, mismatch_count, gap_count
>
> Raises:
>
> ValueError: if query or reference is empty
>
> ValueError: if params is missing required keys
>
> Example:
>
> \>\>\> r = smith_waterman(\"ACGT\", \"ACGT\")
>
> \>\>\> assert r.metrics\[\"identity_pct\"\] == 100.0
>
> **SECTION 21 --- FINAL DELIVERABLES SUMMARY**

**21.1 Complete Module Inventory**

  -------------------------- ------------------ ------------------------------------------------------------------ --------------------------------
  **File**                   **Lines (est.)**   **Key Classes / Functions**                                        **Dependencies**

  smith_waterman.py          \~150              smith_waterman(), \_traceback(), \_sw_vectorised()                 numpy, alignment_metrics

  needleman_wunsch.py        \~130              needleman_wunsch(), \_nw_traceback()                               numpy, alignment_metrics

  alignment_metrics.py       \~80               compute_metrics(), passes_thresholds()                             None (stdlib only)

  blast_statistics.py        \~90               bit_score(), e_value(), score_hit()                                math (stdlib)

  substitution_matrices.py   \~70               load_matrix(), score_pair()                                        functools, json, pathlib

  kmer_engine.py             \~120              build_kmer_profile(), kmer_statistics(), compare_kmer_profiles()   collections, numpy

  minhash_engine.py          \~100              build_minhash(), jaccard_similarity(), build_lsh_index()           datasketch

  bwt_engine.py              \~90               build_bwt(), inverse_bwt(), bwt_count_occurrences()                None (stdlib)

  fmindex_engine.py          \~110              FMIndex class: count(), locate()                                   bwt_engine, collections

  bwa_mem_engine.py          \~100              BWAMemEngine class: find_mems(), align()                           fmindex_engine, smith_waterman

  similarity_engine.py       \~100              jaccard(), cosine(), mash_distance(), edit_distance()              numpy, scipy

  statistics_engine.py       \~90               describe(), z_scores(), confidence_interval(), normalise_score()   numpy, scipy

  result_models.py           \~50               AlgorithmResult dataclass                                          dataclasses, datetime

  sequence_utils.py          \~40               complement(), reverse_complement(), normalise()                    None (stdlib)

  db_writer.py               \~80               write_alignment_result(), write_similarity_metric()                sqlalchemy
  -------------------------- ------------------ ------------------------------------------------------------------ --------------------------------

**21.2 Dependencies**

  ------------------ ------------- ------------------------------------------------------------------
  **Package**        **Version**   **Usage**

  numpy              ≥ 1.26        Vectorised DP matrices, k-mer arrays, stat operations

  scipy              ≥ 1.12        Statistical functions: z-score, t-intervals, dip test

  datasketch         ≥ 1.6         MinHash and LSH index for genome similarity

  biopython          ≥ 1.83        Sequence utilities; substitution matrix data files (BLOSUM, PAM)

  pytest             ≥ 8.0         Test framework

  pytest-benchmark   ≥ 4.0         Performance benchmark harness

  sqlalchemy         ≥ 2.0         DB persistence for algorithm results

  fastapi            ≥ 0.111       REST API service layer

  pydantic           ≥ 2.6         Request/response schema validation
  ------------------ ------------- ------------------------------------------------------------------

**21.3 Implementation Checklist**

  ---------------------- --------------------------------------------------------------------- -------------- --------------------------------------------------------------------------
  **Phase**              **Deliverables**                                                      **Duration**   **Acceptance Criteria**

  1 --- Core alignment   smith_waterman.py, needleman_wunsch.py, alignment_metrics.py          3 days         All known-answer tests pass; SW for 500 bp pair \< 5 ms

  2 --- Statistics       blast_statistics.py, statistics_engine.py, substitution_matrices.py   2 days         Bit score / E-value match BLAST manual reference values ±0.01

  3 --- Similarity       kmer_engine.py, minhash_engine.py, similarity_engine.py               3 days         Jaccard(A,A)=1.0; Jaccard(A,B)∈\[0,1\]; MinHash error ±5% of exact

  4 --- Indexing         bwt_engine.py, fmindex_engine.py, bwa_mem_engine.py                   3 days         FM-Index count/locate match brute-force search on 100 test patterns

  5 --- API              FastAPI routes, Pydantic schemas, DB writer                           2 days         All endpoints return correct responses; alignment stored and retrievable

  6 --- Optimisation     NumPy vectorisation, caching, benchmark suite                         2 days         All benchmark targets met; no regressions in known-answer tests

  7 --- Docs & tests     Docstrings, MkDocs, full test suite, CI setup                         2 days         ≥ 95% coverage; all benchmarks pass in CI; docs build successfully
  ---------------------- --------------------------------------------------------------------- -------------- --------------------------------------------------------------------------