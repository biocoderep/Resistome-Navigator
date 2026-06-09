"""Minimap2 alignment wrapper."""

import subprocess
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

from backend.alignment.base import AlignmentConfig, AlignmentHit, AlignmentResult, BaseAligner


class Minimap2Aligner(BaseAligner):
    """Minimap2-based alignment tool for long-read mapping."""

    def __init__(self, config: Optional[AlignmentConfig] = None):
        """Initialize Minimap2 aligner."""
        if config is None:
            config = AlignmentConfig()
        super().__init__(config)

    def align(
        self,
        query_file: Path,
        reference_db: Path,
        output_file: Path,
        sample_id: UUID = None,
        assembly_id: UUID = None,
        progress_callback=None,
    ) -> AlignmentResult:
        """
        Execute Minimap2 alignment.

        Args:
            query_file: Path to query FASTA file
            reference_db: Path to reference FASTA
            output_file: Path for PAF output
            sample_id: Sample UUID
            assembly_id: Assembly UUID
            progress_callback: Optional progress callback

        Returns:
            AlignmentResult with mapping statistics
        """
        if progress_callback:
            progress_callback(10, "Preparing Minimap2 reference")

        result = AlignmentResult(
            alignment_id=uuid4(),
            sample_id=sample_id or uuid4(),
            assembly_id=assembly_id or uuid4(),
            reference_db=str(reference_db),
            method=self.config.method,
            total_queries=0,
            mapped_queries=0,
            mapped_percent=0.0,
            unmapped_queries=0,
        )

        try:
            # Build minimap2 command
            cmd = [
                "minimap2",
                "-t",
                str(self.config.threads),
                "-x",
                "asm5",  # Assembly-to-reference preset
                "-o",
                str(output_file),
                str(reference_db),
                str(query_file),
            ]

            if progress_callback:
                progress_callback(20, "Running Minimap2 alignment")

            # Execute alignment
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600,
            )

            if process.returncode != 0:
                result.errors.append(f"Minimap2 failed: {process.stderr}")
                return result

            if progress_callback:
                progress_callback(50, "Parsing alignment results")

            # Parse PAF file
            hits = self._parse_paf(output_file)
            result.hits = hits

            if progress_callback:
                progress_callback(80, "Computing statistics")

            # Compute statistics
            result.total_queries = len(set(h.query_name for h in hits))
            result.mapped_queries = len(set(h.query_name for h in hits))
            result.mapped_percent = (
                100.0 * result.mapped_queries / result.total_queries
                if result.total_queries > 0
                else 0.0
            )
            result.stats = {
                "mean_identity": (
                    sum(h.identity_percent for h in hits) / len(hits)
                    if hits
                    else 0.0
                ),
                "mean_alignment_length": (
                    sum(h.alignment_length for h in hits) / len(hits)
                    if hits
                    else 0
                ),
            }

            result.output_file = output_file

            if progress_callback:
                progress_callback(100, "Alignment complete")

        except subprocess.TimeoutExpired:
            result.errors.append("Minimap2 alignment timed out after 1 hour")
        except Exception as e:
            result.errors.append(f"Alignment error: {str(e)}")

        return result

    def _parse_paf(self, paf_file: Path) -> list[AlignmentHit]:
        """Parse PAF file and extract hits."""
        hits = []

        try:
            with open(paf_file) as f:
                for line in f:
                    if line.startswith("#"):
                        continue

                    fields = line.strip().split("\t")
                    if len(fields) < 12:
                        continue

                    # PAF format fields
                    query_name = fields[0]
                    query_length = int(fields[1])
                    query_start = int(fields[2])
                    query_end = int(fields[3])
                    strand = fields[4]
                    subject_name = fields[5]
                    subject_length = int(fields[6])
                    subject_start = int(fields[7])
                    subject_end = int(fields[8])
                    match_length = int(fields[9])
                    alignment_length = int(fields[10])
                    mapq = int(fields[11])

                    # Extract identity from optional fields
                    identity_percent = 100.0
                    for field in fields[12:]:
                        if field.startswith("de:"):
                            # Divergence estimate
                            divergence = float(field.split(":")[-1])
                            identity_percent = 100.0 * (1.0 - divergence)

                    hit = AlignmentHit(
                        query_name=query_name,
                        subject_name=subject_name,
                        query_start=query_start,
                        query_end=query_end,
                        subject_start=subject_start,
                        subject_end=subject_end,
                        match_length=match_length,
                        identity_percent=identity_percent,
                        alignment_length=alignment_length,
                        bit_score=mapq * 10.0,
                    )
                    hits.append(hit)

        except Exception as e:
            return []

        return hits

    def parse_output(self, output_file: Path) -> list[AlignmentHit]:
        """Parse PAF output file."""
        return self._parse_paf(output_file)
