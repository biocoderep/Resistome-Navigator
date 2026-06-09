"""FASTA structure and character validation."""

from __future__ import annotations

import gzip
from pathlib import Path

from Bio import SeqIO

from .models import ValidationError

# IUPAC nucleotide codes
IUPAC = set("ATGCNRYSWKMBDHVatgcnryswkmbdhv")


class InputValidator:
    """Validates FASTA file structure and content."""

    def __init__(self, min_contig_length_bp: int = 200):
        """Initialize validator.
        
        Args:
            min_contig_length_bp: Minimum allowed contig length in bp.
        """
        self.min_contig_length_bp = min_contig_length_bp
        self.errors: list[ValidationError] = []
        self.warnings: list[ValidationError] = []

    def validate(self, file_path: Path) -> tuple[bool, list[ValidationError], list[ValidationError]]:
        """Validate FASTA file structure and content.
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        # Check file exists
        if not file_path.exists():
            self.errors.append(
                ValidationError(
                    code="FILE_EMPTY",
                    detail=f"File not found: {file_path}",
                )
            )
            return False, self.errors, self.warnings

        # Check file size
        file_size = file_path.stat().st_size
        if file_size == 0:
            self.errors.append(
                ValidationError(
                    code="FILE_EMPTY",
                    detail="File is empty (0 bytes)",
                )
            )
            return False, self.errors, self.warnings

        try:
            seen_ids = set()
            record_count = 0

            # Determine if gzipped
            opener = gzip.open if str(file_path).endswith(".gz") else open

            with opener(file_path, "rt", encoding="utf-8", errors="strict") as fh:
                # Check first character is ">"
                first_char = fh.read(1)
                if not first_char:
                    self.errors.append(
                        ValidationError(
                            code="FILE_EMPTY",
                            detail="File is empty",
                        )
                    )
                    return False, self.errors, self.warnings

                if first_char != ">":
                    self.errors.append(
                        ValidationError(
                            code="NOT_FASTA_FORMAT",
                            detail=f"First non-whitespace character should be '>'; found '{first_char}'",
                        )
                    )
                    return False, self.errors, self.warnings

                # Rewind and parse full file
                fh.seek(0)

            # Parse with BioPython
            try:
                with opener(file_path, "rt", encoding="utf-8", errors="strict") as fh:
                    for rec in SeqIO.parse(fh, "fasta"):
                        record_count += 1
                        seq_str = str(rec.seq).upper()

                        # Check for duplicate IDs
                        if rec.id in seen_ids:
                            self.errors.append(
                                ValidationError(
                                    code="DUPLICATE_HEADER",
                                    contig=rec.id,
                                    detail=f"Duplicate sequence ID: {rec.id}",
                                )
                            )
                            return False, self.errors, self.warnings

                        seen_ids.add(rec.id)

                        # Check for empty sequence
                        if len(seq_str) == 0:
                            self.errors.append(
                                ValidationError(
                                    code="EMPTY_SEQUENCE",
                                    contig=rec.id,
                                    detail=f"Sequence for {rec.id} is empty",
                                )
                            )
                            continue

                        # Check for invalid nucleotides
                        invalid_chars = set(seq_str) - IUPAC
                        if invalid_chars:
                            self.errors.append(
                                ValidationError(
                                    code="INVALID_NUCLEOTIDE",
                                    contig=rec.id,
                                    detail=f"Invalid nucleotide characters: {invalid_chars}",
                                )
                            )
                            return False, self.errors, self.warnings

                        # Check minimum contig length
                        if len(seq_str) < self.min_contig_length_bp:
                            self.warnings.append(
                                ValidationError(
                                    code="CONTIG_TOO_SHORT",
                                    contig=rec.id,
                                    detail=f"Contig length {len(seq_str)} bp is below minimum {self.min_contig_length_bp} bp",
                                )
                            )

            except ValueError as e:
                self.errors.append(
                    ValidationError(
                        code="NOT_FASTA_FORMAT",
                        detail=f"FASTA parsing error: {str(e)}",
                    )
                )
                return False, self.errors, self.warnings

            if record_count == 0:
                self.errors.append(
                    ValidationError(
                        code="FILE_EMPTY",
                        detail="No valid FASTA records found in file",
                    )
                )
                return False, self.errors, self.warnings

        except UnicodeDecodeError as e:
            self.errors.append(
                ValidationError(
                    code="ENCODING_ERROR",
                    detail=f"File encoding error: {str(e)}",
                )
            )
            return False, self.errors, self.warnings

        except Exception as e:
            self.errors.append(
                ValidationError(
                    code="TRUNCATED_FILE",
                    detail=f"Unexpected error during parsing: {str(e)}",
                )
            )
            return False, self.errors, self.warnings

        return len(self.errors) == 0, self.errors, self.warnings


__all__ = ["InputValidator", "IUPAC"]
