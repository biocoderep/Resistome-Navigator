"""Assembly statistics computation (N50, contig counts, etc.)."""

from __future__ import annotations

import gzip
import statistics
from pathlib import Path

from Bio import SeqIO

from .models import AssemblyMetrics, ContigData


def n_stat(lengths: list[int], fraction: float) -> int:
    """Compute Nx statistic (e.g., N50 when fraction=0.5).
    
    Args:
        lengths: List of contig lengths in bp.
        fraction: Fraction threshold (0.5 for N50, 0.9 for N90, etc.).
    
    Returns:
        Nx statistic in bp.
    """
    if not lengths:
        return 0
    
    sorted_lens = sorted(lengths, reverse=True)
    target = sum(sorted_lens) * fraction
    cumsum = 0
    
    for length in sorted_lens:
        cumsum += length
        if cumsum >= target:
            return length
    
    return 0


def l_stat(lengths: list[int], fraction: float) -> int:
    """Compute Lx statistic (number of contigs at Nx).
    
    Args:
        lengths: List of contig lengths in bp.
        fraction: Fraction threshold (0.5 for L50, 0.9 for L90, etc.).
    
    Returns:
        Number of contigs required to reach Nx.
    """
    if not lengths:
        return 0
    
    sorted_lens = sorted(lengths, reverse=True)
    target = sum(sorted_lens) * fraction
    cumsum = 0
    count = 0
    
    for length in sorted_lens:
        count += 1
        cumsum += length
        if cumsum >= target:
            return count
    
    return len(sorted_lens)


def compute_assembly_metrics(
    file_path: Path, sample_id: str, assembly_id: str | None = None
) -> tuple[AssemblyMetrics, list[ContigData]]:
    """Compute assembly statistics from FASTA file.
    
    Args:
        file_path: Path to FASTA file.
        sample_id: Sample UUID as string.
        assembly_id: Assembly UUID as string (optional).
    
    Returns:
        Tuple of (AssemblyMetrics, list of ContigData objects).
    """
    opener = gzip.open if str(file_path).endswith(".gz") else open
    
    contigs: list[ContigData] = []
    lengths: list[int] = []
    total_length = 0
    total_gc = 0
    total_n = 0
    total_bases = 0
    
    with opener(file_path, "rt", encoding="utf-8") as fh:
        for record in SeqIO.parse(fh, "fasta"):
            seq_str = str(record.seq).upper()
            seq_len = len(seq_str)
            
            lengths.append(seq_len)
            total_length += seq_len
            
            # Count bases
            gc_count = seq_str.count("G") + seq_str.count("C")
            n_count = seq_str.count("N")
            total_gc += gc_count
            total_n += n_count
            
            # Count only defined bases (A,T,G,C) for N%
            defined_bases = seq_str.count("A") + seq_str.count("T") + seq_str.count("G") + seq_str.count("C")
            total_bases += seq_len  # Total includes N
            
            gc_pct = (gc_count / seq_len * 100) if seq_len > 0 else 0.0
            n_pct = (n_count / seq_len * 100) if seq_len > 0 else 0.0
            
            # Compute Shannon entropy (Phase 2, but include basic version)
            entropy = _shannon_entropy(seq_str)
            
            contigs.append(
                ContigData(
                    contig_id=record.id,
                    sequence=seq_str,
                    length=seq_len,
                    gc_pct=gc_pct,
                    n_pct=n_pct,
                    entropy=entropy,
                )
            )
    
    # Compute statistics
    contig_count = len(lengths)
    mean_length = statistics.mean(lengths) if lengths else 0.0
    median_length = statistics.median(lengths) if lengths else 0.0
    max_length = max(lengths) if lengths else 0
    min_length = min(lengths) if lengths else 0
    
    n50 = n_stat(lengths, 0.5)
    n90 = n_stat(lengths, 0.9)
    l50 = l_stat(lengths, 0.5)
    
    gc_pct = (total_gc / total_length * 100) if total_length > 0 else 0.0
    n_pct = (total_n / total_length * 100) if total_length > 0 else 0.0
    
    metrics = AssemblyMetrics(
        sample_id=sample_id,
        assembly_id=assembly_id,
        total_length_bp=total_length,
        contig_count=contig_count,
        mean_contig_bp=mean_length,
        median_contig_bp=median_length,
        max_contig_bp=max_length,
        min_contig_bp=min_length,
        n50_bp=n50,
        n90_bp=n90,
        l50=l50,
        gc_percent=gc_pct,
        n_percent=n_pct,
        assembly_span_bp=total_length,
    )
    
    return metrics, contigs


def _shannon_entropy(seq: str) -> float:
    """Compute Shannon entropy of sequence.
    
    H = -Σ p(x) log₂(p(x)) where p(x) = frequency of base x
    """
    import math
    
    if len(seq) == 0:
        return 0.0
    
    # Count base frequencies
    counts = {}
    for base in "ATGCN":
        count = seq.count(base)
        if count > 0:
            counts[base] = count
    
    # Compute entropy
    entropy = 0.0
    total = len(seq)
    
    for count in counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    
    return entropy


__all__ = ["compute_assembly_metrics", "n_stat", "l_stat"]
