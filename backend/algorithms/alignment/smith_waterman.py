"""Smith-Waterman and Needleman-Wunsch alignment algorithms stub."""

from dataclasses import dataclass
from typing import Dict, Any

from Bio import Align

@dataclass
class AlignmentResult:
    query_seq: str
    target_seq: str
    alignment: str
    score: float
    metrics: Dict[str, Any]


def smith_waterman(query: str, target: str) -> AlignmentResult:
    """Local alignment (Smith-Waterman) using BioPython."""
    aligner = Align.PairwiseAligner()
    aligner.mode = 'local'
    aligner.match_score = 2
    aligner.mismatch_score = -1
    aligner.open_gap_score = -5
    aligner.extend_gap_score = -1
    
    alignments = aligner.align(query, target)
    if not alignments:
        return AlignmentResult(query, target, "", 0.0, {"identity_pct": 0.0})
    
    best_aln = alignments[0]
    identity = (best_aln.counts().identities / max(len(query), len(target))) * 100
    
    return AlignmentResult(
        query_seq=query,
        target_seq=target,
        alignment=str(best_aln),
        score=best_aln.score,
        metrics={"identity_pct": identity}
    )

def needleman_wunsch(query: str, target: str) -> AlignmentResult:
    """Global alignment (Needleman-Wunsch) using BioPython."""
    aligner = Align.PairwiseAligner()
    aligner.mode = 'global'
    aligner.match_score = 2
    aligner.mismatch_score = -1
    aligner.open_gap_score = -5
    aligner.extend_gap_score = -1
    
    alignments = aligner.align(query, target)
    if not alignments:
        return AlignmentResult(query, target, "", 0.0, {"identity_pct": 0.0})
    
    best_aln = alignments[0]
    identity = (best_aln.counts().identities / max(len(query), len(target))) * 100
    
    # We need the aligned strings (with gaps) to do variant calling.
    # A Bio.Align.Alignment object format prints as three lines: seqA, match/mismatch, seqB
    # best_aln[0] is the first argument (query), best_aln[1] is the second argument (target)
    query_aligned = best_aln[0]
    target_aligned = best_aln[1]
    
    return AlignmentResult(
        query_seq=query_aligned,
        target_seq=target_aligned,
        alignment=str(best_aln),
        score=best_aln.score,
        metrics={"identity_pct": identity}
    )
