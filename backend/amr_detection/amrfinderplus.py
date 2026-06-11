"""AMRFinderPlus AMR detection wrapper."""

import json
import subprocess
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

from backend.amr_detection.base import (
    AMRConfig,
    AMRDetectionResult,
    AMRHit,
    BaseAMRDetector,
    ConfidenceLevel,
    ResistanceClass,
)


class AMRFinderPlusDetector(BaseAMRDetector):
    """AMRFinderPlus-based AMR detection tool."""

    def __init__(self, config: Optional[AMRConfig] = None):
        """Initialize AMRFinderPlus detector."""
        if config is None:
            config = AMRConfig()
        super().__init__(config)

    def detect(
        self,
        assembly_file: Path,
        output_dir: Path,
        sample_id: UUID = None,
        assembly_id: UUID = None,
        progress_callback=None,
    ) -> AMRDetectionResult:
        """
        Execute AMRFinderPlus AMR detection.

        Args:
            assembly_file: Path to assembly FASTA
            output_dir: Directory for output files
            sample_id: Sample UUID
            assembly_id: Assembly UUID
            progress_callback: Optional progress callback

        Returns:
            AMRDetectionResult with AMR hits
        """
        if progress_callback:
            progress_callback(10, "Initializing AMRFinderPlus")

        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "amrfinderplus_report.tsv"

        result = AMRDetectionResult(
            detection_id=uuid4(),
            sample_id=sample_id or uuid4(),
            assembly_id=assembly_id or uuid4(),
            tools_run=["amrfinderplus"],
            total_amr_genes=0,
            unique_gene_families=0,
            resistance_classes=[],
        )

        try:
            # Build AMRFinderPlus command
            cmd = [
                "amrfinder",
                "-n",
                str(assembly_file),
                "-o",
                str(output_file),
                "-d",
                "database_dir",  # Requires AMRFINDER_DB env var set
                "-t",
                "nucleotide",
                "--report_common",
                "--plus"  # <--- NEW FLAG added here
            ]

            if progress_callback:
                progress_callback(20, "Running AMRFinderPlus analysis")

            # Execute AMRFinderPlus
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600,
            )

            if process.returncode != 0:
                result.errors.append(f"AMRFinderPlus failed: {process.stderr}")
                return result

            if progress_callback:
                progress_callback(50, "Parsing AMRFinderPlus results")

            # Parse TSV results
            if output_file.exists():
                hits, virulence_hits = self._parse_amrfinderplus_tsv(output_file)
                result.hits = hits
                result.virulence_hits = virulence_hits

                if progress_callback:
                    progress_callback(80, "Computing AMR statistics")

                # Compute statistics
                result.total_amr_genes = len(hits)
                result.unique_gene_families = len(set(h.gene_family for h in hits))
                result.resistance_classes = list(
                    set(h.resistance_class for h in hits)
                )

            result.output_files["amrfinderplus_tsv"] = str(output_file)

            if progress_callback:
                progress_callback(100, "AMRFinderPlus analysis complete")

        except subprocess.TimeoutExpired:
            result.errors.append("AMRFinderPlus analysis timed out after 1 hour")
        except Exception as e:
            result.errors.append(f"Analysis error: {str(e)}")

        return result

    def _parse_amrfinderplus_tsv(self, tsv_file: Path) -> tuple[list[AMRHit], list[dict]]:
        """Parse AMRFinderPlus TSV output."""
        hits = []
        virulence_hits = []

        try:
            with open(tsv_file) as f:
                lines = f.readlines()

            # Skip header
            if not lines:
                return [], []

            header = lines[0].strip().split("\t")
            header_map = {name: idx for idx, name in enumerate(header)}

            for line in lines[1:]:
                fields = line.strip().split("\t")
                if len(fields) < len(header):
                    continue

                # Parse fields
                protein_name = fields[header_map.get("Protein_name", 0)]
                gene_symbol = fields[header_map.get("Gene_symbol", 1)]
                sequence_name = fields[header_map.get("Sequence_name", 2)]
                scope = fields[header_map.get("Scope", 3)]
                element_type = fields[header_map.get("Element_type", 4)]
                subclass = fields[header_map.get("Subclass", 5)] if "Subclass" in header_map else ""

                if element_type == "VIRULENCE":
                    virulence_hits.append({
                        "gene_name": gene_symbol or protein_name,
                        "virulence_factor": subclass or protein_name,
                        "mechanism": "Unknown",
                        "contig_id": sequence_name,
                        "start_position": 0,
                        "end_position": 0,
                        "identity_percent": 100.0,
                        "coverage_percent": 100.0,
                        "database_source": "AMRFinderPlus"
                    })
                    continue

                # Determine confidence
                if scope == "Core":
                    confidence = ConfidenceLevel.HIGH
                elif scope == "Plus":
                    confidence = ConfidenceLevel.MEDIUM
                else:
                    confidence = ConfidenceLevel.LOW

                # Determine resistance class
                resistance_class = ResistanceClass.OTHER
                if "Aminoglycoside" in protein_name:
                    resistance_class = ResistanceClass.AMINOGLYCOSIDES
                elif "Beta-lactam" in protein_name:
                    resistance_class = ResistanceClass.BETA_LACTAMS
                elif "Fluoroquinolone" in protein_name:
                    resistance_class = ResistanceClass.FLUOROQUINOLONES
                elif "Tetracycline" in protein_name:
                    resistance_class = ResistanceClass.TETRACYCLINES
                elif "Macrolide" in protein_name:
                    resistance_class = ResistanceClass.MACROLIDES

                hit = AMRHit(
                    gene_name=gene_symbol or protein_name,
                    gene_family=protein_name,
                    resistance_class=resistance_class,
                    contig_id=sequence_name,
                    start_position=0,  # Not in AMRFinderPlus output
                    end_position=0,
                    gene_length=0,
                    identity_percent=100.0,
                    coverage_percent=100.0,
                    tool_name="amrfinderplus",
                    confidence=confidence,
                    phenotype=element_type,
                )
                hits.append(hit)

        except Exception as e:
            return [], []

        return hits, virulence_hits

    def parse_results(self, output_dir: Path) -> tuple[list[AMRHit], list[dict]]:
        """Parse AMRFinderPlus results."""
        tsv_file = output_dir / "amrfinderplus_report.tsv"
        if tsv_file.exists():
            return self._parse_amrfinderplus_tsv(tsv_file)
        return [], []
