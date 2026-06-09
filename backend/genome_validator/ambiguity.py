"""Ambiguous base analysis (N% and ambiguity code detection)."""

from __future__ import annotations

import re

from .models import AmbiguityReport, ContigData, NRun, PerContigAmbiguity, ValidationError


def analyze_ambiguity(
    contigs: list[ContigData],
    n_warn_threshold: float = 1.0,
    n_fail_threshold: float = 5.0,
) -> tuple[AmbiguityReport, list[ValidationError]]:
    """Analyze ambiguous bases (N and IUPAC ambiguity codes).
    
    Args:
        contigs: List of ContigData objects.
        n_warn_threshold: N% threshold for WARNING.
        n_fail_threshold: N% threshold for FAIL.
    
    Returns:
        Tuple of (AmbiguityReport, list of errors/warnings).
    """
    warnings: list[ValidationError] = []
    
    total_n = 0
    total_bases = 0
    per_contig_n: list[PerContigAmbiguity] = []
    longest_n_run: NRun | None = None
    max_run_length = 0
    
    # Track other IUPAC ambiguity codes
    other_ambig_count = 0
    
    for contig in contigs:
        seq = contig.sequence
        n_count = seq.count("N")
        total_n += n_count
        total_bases += len(seq)
        
        n_pct = (n_count / len(seq) * 100) if len(seq) > 0 else 0.0
        per_contig_n.append(
            PerContigAmbiguity(
                contig_id=contig.contig_id,
                n_count=n_count,
                n_pct=n_pct,
            )
        )
        
        # Count other IUPAC ambiguity codes
        for char in "RYSWKMBDHV":
            other_ambig_count += seq.count(char)
        
        # Find longest N-run in this contig
        if "N" in seq:
            for match in re.finditer(r"N+", seq):
                run_length = len(match.group())
                if run_length > max_run_length:
                    max_run_length = run_length
                    longest_n_run = NRun(
                        contig_id=contig.contig_id,
                        run_length=run_length,
                        position=match.start(),
                    )
    
    # Compute overall N%
    n_pct = (total_n / total_bases * 100) if total_bases > 0 else 0.0
    other_ambig_pct = (other_ambig_count / total_bases * 100) if total_bases > 0 else 0.0
    
    # Determine status
    if n_pct > n_fail_threshold:
        n_status = "FAIL"
        warnings.append(
            ValidationError(
                code="N_PERCENT_TOO_HIGH",
                detail=f"N% is {n_pct:.2f}%, exceeds fail threshold of {n_fail_threshold}%",
            )
        )
    elif n_pct > n_warn_threshold:
        n_status = "WARNING"
        warnings.append(
            ValidationError(
                code="N_PERCENT_WARNING",
                detail=f"N% is {n_pct:.2f}%, exceeds warning threshold of {n_warn_threshold}%",
            )
        )
    else:
        n_status = "PASS"
    
    return (
        AmbiguityReport(
            total_bases=total_bases,
            n_count=total_n,
            n_percent=n_pct,
            n_status=n_status,
            longest_n_run=longest_n_run,
            per_contig_n=per_contig_n,
            other_ambiguity_pct=other_ambig_pct,
        ),
        warnings,
    )


__all__ = ["analyze_ambiguity"]
