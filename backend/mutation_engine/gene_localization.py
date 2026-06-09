"""Gene localization engine - Module 1D v1.0.0"""

import json
from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path

from Bio import SeqIO
from Bio.Seq import Seq

from ..algorithms.alignment.needleman_wunsch import needleman_wunsch
from ..algorithms.utilities.result_models import AlgorithmResult as AlignmentResult
from ..algorithms.search.fmindex_engine import FMIndex

@dataclass
class BlastHit:
    """Temporary class for BLAST pre-screen hits."""
    gene_name: str
    contig_id: str
    start: int
    end: int
    strand: str
    query_seq: str
    identity: float

@dataclass
class GeneLocation:
    gene_name: str
    contig_id: str
    start: int  # 1-based inclusive
    end: int    # 1-based inclusive
    strand: str # "+" or "-"
    identity_pct: float
    coverage_pct: float
    extracted_seq: str # coding sequence from assembly (same strand as reference)


def _blast_localise(fasta_path: Path, references: Dict[str, str], min_identity: float = 70.0) -> List[BlastHit]:
    """
    Stub for BLAST pre-screening. 
    In a real implementation, this would invoke BLAST+ or an equivalent fast heuristic.
    Here we do a naive sliding window or standard local alignment as a fallback.
    For MVP/stub purposes, we will use Smith-Waterman or direct string search.
    """
    hits = []
    
    records = list(SeqIO.parse(fasta_path, "fasta"))
    
    for gene_name, ref_seq in references.items():
        # A true BLAST would search the entire genome efficiently.
        # For this stub, we will iterate over contigs and do a fast subsequence scan 
        # or just fallback to NW/SW if the genome is small.
        # Given this is a stub for real genome sizes, we simulate a perfect hit if found,
        # or we just use our FMIndex stub on the full contig.
        
        for record in records:
            # Check forward strand
            idx = FMIndex(str(record.seq).upper())
            # For simplicity, we search the first 10 chars as a seed
            seed = ref_seq[:10].upper()
            if len(seed) > 0:
                pos_list = idx.locate(seed)
                for pos in pos_list:
                    # Found a potential hit on forward strand
                    start = pos
                    end = min(len(record.seq), start + len(ref_seq) + 100)
                    query_seq = str(record.seq[start-1:end])
                    hits.append(BlastHit(
                        gene_name=gene_name, contig_id=record.id,
                        start=start, end=end, strand="+", 
                        query_seq=query_seq, identity=100.0
                    ))
            
            # Check reverse strand
            rev_seq = str(record.seq.reverse_complement()).upper()
            idx_rev = FMIndex(rev_seq)
            if len(seed) > 0:
                pos_list = idx_rev.locate(seed)
                for pos in pos_list:
                    start = pos
                    end = min(len(rev_seq), start + len(ref_seq) + 100)
                    query_seq = rev_seq[start-1:end]
                    hits.append(BlastHit(
                        gene_name=gene_name, contig_id=record.id,
                        start=len(record.seq) - end + 1, end=len(record.seq) - start + 1, 
                        strand="-", query_seq=query_seq, identity=100.0
                    ))
                    
    return hits

def _build_location(hit: BlastHit, nw_result: AlignmentResult, ref_len: int) -> GeneLocation:
    """Build a GeneLocation object from a hit and its refined alignment."""
    # Compute coverage based on how much of the reference was aligned without huge gaps
    r_aln = nw_result.metadata.get("r_aln", "")
    aligned_ref_bases = len(r_aln.replace("-", ""))
    coverage = (aligned_ref_bases / ref_len) * 100 if ref_len > 0 else 0.0
    
    # Clean the query sequence from gaps for the extracted_seq
    q_aln = nw_result.metadata.get("q_aln", "")
    extracted = q_aln.replace("-", "")
    
    return GeneLocation(
        gene_name=hit.gene_name,
        contig_id=hit.contig_id,
        start=hit.start,
        end=hit.end,
        strand=hit.strand,
        identity_pct=nw_result.metrics.get("identity_pct", 0.0),
        coverage_pct=coverage,
        extracted_seq=extracted
    )

def localise_genes(fasta_path: str, references: Dict[str, str], 
                   min_identity: float = 85.0, min_coverage: float = 80.0) -> List[GeneLocation]:
    """
    Locate target resistance genes using BLAST for speed, with SW/NW fallback.
    references: {gene_name: reference_cds_sequence}
    """
    results = []
    fasta_file = Path(fasta_path)
    if not fasta_file.exists():
        return results

    # Step 1: BLAST pre-screening (fast; low threshold)
    blast_hits = _blast_localise(fasta_file, references, min_identity=70.0)
    
    # Step 2: Refine candidate regions with NW alignment
    for hit in blast_hits:
        ref_seq = references[hit.gene_name]
        # Align query vs reference
        nw_result = needleman_wunsch(hit.query_seq.upper(), ref_seq.upper())
        
        identity = nw_result.metrics.get("identity_pct", 0.0)
        
        # Calculate coverage
        r_aln = nw_result.metadata.get("r_aln", "")
        aligned_ref_bases = len(r_aln.replace("-", ""))
        coverage = (aligned_ref_bases / len(ref_seq)) * 100 if len(ref_seq) > 0 else 0.0
        
        if identity >= min_identity and coverage >= min_coverage:
            results.append(_build_location(hit, nw_result, len(ref_seq)))
            
    return results
