"""GC content analysis including per-contig analysis and outlier detection."""

from __future__ import annotations

import statistics

from .models import ContigData, GCAnalysisReport, GCOutlier, PerContigGC


def analyze_gc(contigs: list[ContigData]) -> GCAnalysisReport:
    """Analyze GC content across assembly.
    
    Args:
        contigs: List of ContigData objects with computed GC percentages.
    
    Returns:
        GCAnalysisReport with whole-genome, per-contig, and outlier information.
    """
    if not contigs:
        return GCAnalysisReport(
            whole_genome_gc_pct=0.0,
            mean_contig_gc_pct=0.0,
            gc_variance=0.0,
            gc_std_dev=0.0,
            per_contig=[],
            outlier_contigs=[],
            flag="OK",
        )
    
    # Whole genome GC (computed from concatenated sequences)
    total_gc = 0
    total_non_n = 0
    
    for contig in contigs:
        seq = contig.sequence
        total_gc += seq.count("G") + seq.count("C")
        total_non_n += len(seq.replace("N", ""))
    
    whole_genome_gc_pct = (total_gc / total_non_n * 100) if total_non_n > 0 else 0.0
    
    # Per-contig GC values
    per_contig_gc_list = [contig.gc_pct for contig in contigs]
    per_contig = [
        PerContigGC(
            contig_id=contig.contig_id,
            length=contig.length,
            gc_pct=contig.gc_pct,
        )
        for contig in contigs
    ]
    
    # Compute mean and variance
    mean_gc = statistics.mean(per_contig_gc_list) if per_contig_gc_list else 0.0
    variance = statistics.variance(per_contig_gc_list) if len(per_contig_gc_list) > 1 else 0.0
    std_dev = statistics.stdev(per_contig_gc_list) if len(per_contig_gc_list) > 1 else 0.0
    
    # Detect outliers (GC deviates > 3 SD from mean)
    outlier_contigs: list[GCOutlier] = []
    threshold = 3.0
    
    if std_dev > 0:
        for contig in contigs:
            deviation_sd = abs(contig.gc_pct - mean_gc) / std_dev
            if deviation_sd > threshold:
                outlier_contigs.append(
                    GCOutlier(
                        contig_id=contig.contig_id,
                        length=contig.length,
                        gc_pct=contig.gc_pct,
                        deviation_sd=deviation_sd,
                    )
                )
    
    # Determine flag
    flag = "OK"
    flag_reason = None
    
    if outlier_contigs:
        flag = "CONTAMINATION_SUSPECTED"
        outlier_ids = ", ".join([o.contig_id for o in outlier_contigs])
        flag_reason = f"Contigs with unusual GC content detected: {outlier_ids}"
    
    return GCAnalysisReport(
        whole_genome_gc_pct=whole_genome_gc_pct,
        mean_contig_gc_pct=mean_gc,
        gc_variance=variance,
        gc_std_dev=std_dev,
        per_contig=per_contig,
        outlier_contigs=outlier_contigs,
        flag=flag,
        flag_reason=flag_reason,
    )


__all__ = ["analyze_gc"]
