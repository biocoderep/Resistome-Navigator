"""Genome size validation against expected ranges."""

from __future__ import annotations

from .models import GenomeSizeReport, ValidationError


# Expected genome size ranges by organism (in Mb)
SPECIES_SIZE_RANGES = {
    "Escherichia coli": (4.5, 5.8),
    "Salmonella enterica": (4.5, 5.5),
    "Staphylococcus aureus": (2.7, 3.0),
    "Pseudomonas aeruginosa": (6.0, 7.0),
    "Klebsiella pneumoniae": (5.0, 6.5),
    "Acinetobacter baumannii": (3.5, 4.2),
    "Enterococcus faecium": (2.5, 3.2),
}

# Default ranges for unknown species
DEFAULT_MIN_MB = 0.5
DEFAULT_MAX_MB = 15.0


def validate_genome_size(
    total_length_bp: int,
    species: str | None = None,
) -> tuple[GenomeSizeReport, list[ValidationError]]:
    """Validate genome size against expected ranges.
    
    Args:
        total_length_bp: Total assembly length in bp.
        species: Species name if provided.
    
    Returns:
        Tuple of (GenomeSizeReport, list of errors).
    """
    warnings: list[ValidationError] = []
    
    assembly_size_mb = total_length_bp / 1_000_000
    
    # Get expected range
    if species and species in SPECIES_SIZE_RANGES:
        expected_min, expected_max = SPECIES_SIZE_RANGES[species]
    else:
        expected_min = DEFAULT_MIN_MB
        expected_max = DEFAULT_MAX_MB
    
    # Determine status
    if assembly_size_mb < 0.2:
        status = "FAIL"
        warnings.append(
            ValidationError(
                code="GENOME_TOO_SMALL",
                detail=f"Assembly size {assembly_size_mb:.2f} Mb is below absolute minimum 0.2 Mb",
            )
        )
    elif assembly_size_mb < expected_min * 0.8:
        status = "WARNING"
        warnings.append(
            ValidationError(
                code="GENOME_SMALL",
                detail=f"Assembly size {assembly_size_mb:.2f} Mb is below expected range {expected_min:.1f}--{expected_max:.1f} Mb",
            )
        )
    elif assembly_size_mb > 15.0:
        status = "FAIL"
        warnings.append(
            ValidationError(
                code="GENOME_TOO_LARGE",
                detail=f"Assembly size {assembly_size_mb:.2f} Mb exceeds maximum 15 Mb (possible contamination/eukaryotic DNA)",
            )
        )
    elif assembly_size_mb > expected_max * 1.2:
        status = "WARNING"
        warnings.append(
            ValidationError(
                code="GENOME_LARGE",
                detail=f"Assembly size {assembly_size_mb:.2f} Mb exceeds expected range {expected_min:.1f}--{expected_max:.1f} Mb",
            )
        )
    else:
        status = "PASS"
    
    return (
        GenomeSizeReport(
            assembly_size_mb=assembly_size_mb,
            expected_min_mb=expected_min,
            expected_max_mb=expected_max,
            size_status=status,
            size_percentile_for_species=50.0,  # Placeholder
        ),
        warnings,
    )


__all__ = ["validate_genome_size", "SPECIES_SIZE_RANGES"]
