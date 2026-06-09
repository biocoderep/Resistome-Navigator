"""BWA alignment wrapper."""

import subprocess
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

from backend.alignment.base import AlignmentConfig, AlignmentHit, AlignmentResult, BaseAligner


class BWAAligner(BaseAligner):
    """BWA-based alignment tool for both short and long reads."""

    def __init__(self, config: Optional[AlignmentConfig] = None):
        """Initialize BWA aligner."""
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
        Execute BWA alignment.

        Args:
            query_file: Path to query FASTA file
            reference_db: Path to BWA index (FASTA)
            output_file: Path for SAM/BAM output
            sample_id: Sample UUID
            assembly_id: Assembly UUID
            progress_callback: Optional progress callback

        Returns:
            AlignmentResult with mapping statistics
        """
        if progress_callback:
            progress_callback(10, "Indexing reference with BWA")

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
            # Index reference if needed
            if not Path(f"{reference_db}.bwt").exists():
                index_cmd = ["bwa", "index", str(reference_db)]
                subprocess.run(index_cmd, capture_output=True, timeout=3600)

            # Build BWA command
            cmd = [
                "bwa",
                "mem",
                "-t",
                str(self.config.threads),
                "-M",  # Mark shorter hits as secondary
                str(reference_db),
                str(query_file),
            ]

            if progress_callback:
                progress_callback(20, "Running BWA alignment")

            # Execute alignment
            with open(output_file, "w") as out:
                process = subprocess.run(
                    cmd,
                    stdout=out,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=3600,
                )

            if process.returncode != 0:
                result.errors.append(f"BWA failed: {process.stderr}")
                return result

            if progress_callback:
                progress_callback(50, "Parsing alignment results")

            # Parse SAM file
            hits = self._parse_sam(output_file)
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
            result.errors.append("BWA alignment timed out after 1 hour")
        except Exception as e:
            result.errors.append(f"Alignment error: {str(e)}")

        return result

    def _parse_sam(self, sam_file: Path) -> list[AlignmentHit]:
        """Parse SAM file and extract hits."""
        hits = []

        try:
            with open(sam_file) as f:
                for line in f:
                    if line.startswith("@"):
                        continue

                    fields = line.strip().split("\t")
                    if len(fields) < 11:
                        continue

                    # SAM format fields
                    query_name = fields[0]
                    flag = int(fields[1])
                    subject_name = fields[2]
                    subject_start = int(fields[3])
                    mapq = int(fields[4])
                    cigar = fields[5]
                    query_seq = fields[9]

                    # Skip unmapped reads
                    if flag & 4:
                        continue

                    # Calculate alignment length from CIGAR
                    import re

                    alignment_length = sum(
                        int(x) for x in re.findall(r"(\d+)[MDI=X]", cigar)
                    )

                    hit = AlignmentHit(
                        query_name=query_name,
                        subject_name=subject_name,
                        query_start=0,
                        query_end=len(query_seq),
                        subject_start=subject_start,
                        subject_end=subject_start + alignment_length,
                        match_length=alignment_length,
                        identity_percent=min(100.0, 60.0 + mapq),
                        alignment_length=alignment_length,
                        bit_score=mapq * 10.0,
                        cigar=cigar,
                    )
                    hits.append(hit)

        except Exception as e:
            return []

        return hits

    def parse_output(self, output_file: Path) -> list[AlignmentHit]:
        """Parse SAM output file."""
        return self._parse_sam(output_file)
