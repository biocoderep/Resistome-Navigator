"""Contig fragmentation and length distribution analysis."""

from __future__ import annotations

from .models import ContigData, ContigReport


def analyze_contigs(contigs: list[ContigData], total_length_mb: float) -> ContigReport:
    """Analyze contig fragmentation and length distribution.
    
    Args:
        contigs: List of ContigData objects.
        total_length_mb: Total assembly length in Mb.
    
    Returns:
        ContigReport with fragmentation class and length distribution.
    """
    if not contigs:
        return ContigReport(
            contig_count=0,
            fragmentation_class="EXCELLENT",
            length_distribution={},
            short_contig_count_below_500bp=0,
        )
    
    contig_count = len(contigs)
    lengths = [c.length for c in contigs]
    
    # Count length distribution
    distribution = {
        "0-500": 0,
        "500-1000": 0,
        "1000-5000": 0,
        "5000-10000": 0,
        "10000-50000": 0,
        ">50000": 0,
    }
    
    short_count = 0
    n50_from_spec = _compute_n50(lengths)
    
    for length in lengths:
        if length < 500:
            distribution["0-500"] += 1
            short_count += 1
        elif length < 1000:
            distribution["500-1000"] += 1
        elif length < 5000:
            distribution["1000-5000"] += 1
        elif length < 10000:
            distribution["5000-10000"] += 1
        elif length < 50000:
            distribution["10000-50000"] += 1
        else:
            distribution[">50000"] += 1
    
    # Classify fragmentation (adjusted by genome size)
    # Per spec: adjust thresholds by genome size (larger genomes expect more contigs)
    adjusted_threshold = 100 * (total_length_mb / 5.0)
    
    if contig_count < adjusted_threshold and n50_from_spec > 100_000:
        fragmentation_class = "EXCELLENT"
    elif contig_count < adjusted_threshold * 3 and n50_from_spec > 50_000:
        fragmentation_class = "ACCEPTABLE"
    elif contig_count < adjusted_threshold * 10:
        fragmentation_class = "POOR"
    else:
        fragmentation_class = "HIGHLY_FRAGMENTED"
    
    return ContigReport(
        contig_count=contig_count,
        fragmentation_class=fragmentation_class,
        length_distribution=distribution,
        short_contig_count_below_500bp=short_count,
    )


def _compute_n50(lengths: list[int]) -> int:
    """Quick N50 computation for internal use."""
    if not lengths:
        return 0
    sorted_lens = sorted(lengths, reverse=True)
    target = sum(sorted_lens) * 0.5
    cumsum = 0
    for length in sorted_lens:
        cumsum += length
        if cumsum >= target:
            return length
    return 0


__all__ = ["analyze_contigs"]
