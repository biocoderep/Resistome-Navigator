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
    map_resistance_class,
)

SPECIES_MAP = {
    "acinetobacter_baumannii": "Acinetobacter_baumannii",
    "acinetobacter baumannii": "Acinetobacter_baumannii",
    "escherichia": "Escherichia",
    "escherichia coli": "Escherichia",
    "e. coli": "Escherichia",
    "klebsiella_pneumoniae": "Klebsiella_pneumoniae",
    "klebsiella pneumoniae": "Klebsiella_pneumoniae",
    "staphylococcus_aureus": "Staphylococcus_aureus",
    "staphylococcus aureus": "Staphylococcus_aureus",
    "pseudomonas_aeruginosa": "Pseudomonas_aeruginosa",
    "pseudomonas aeruginosa": "Pseudomonas_aeruginosa",
    "salmonella": "Salmonella",
    "enterococcus_faecium": "Enterococcus_faecium",
    "enterococcus faecium": "Enterococcus_faecium",
    "campylobacter": "Campylobacter",
}


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
        species: str = None,
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
                "--plus"  # <--- NEW FLAG added here
            ]
            
            if species:
                mapped_org = SPECIES_MAP.get(species.lower().strip())
                if mapped_org:
                    cmd.extend(["-O", mapped_org])

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
                def get_field(name, fallback_idx):
                    idx = header_map.get(name, fallback_idx)
                    return fields[idx] if idx < len(fields) else ""

                gene_symbol = get_field("Element symbol", 5)
                protein_name = get_field("Element name", 6)
                sequence_name = get_field("Contig id", 1)
                scope = get_field("Scope", 7)
                element_type = get_field("Type", 8)
                subclass = get_field("Subclass", 11)
                class_name = get_field("Class", 10)

                try:
                    start_position = int(get_field("Start", 2))
                except ValueError:
                    start_position = 0

                try:
                    end_position = int(get_field("Stop", 3))
                except ValueError:
                    end_position = 0

                try:
                    coverage_percent = float(get_field("% Coverage of reference", 15))
                except ValueError:
                    coverage_percent = 100.0

                try:
                    identity_percent = float(get_field("% Identity to reference", 16))
                except ValueError:
                    identity_percent = 100.0

                if element_type == "VIRULENCE":
                    virulence_hits.append({
                        "gene_name": gene_symbol or protein_name,
                        "virulence_factor": subclass or protein_name,
                        "mechanism": "Unknown",
                        "contig_id": sequence_name,
                        "start_position": start_position,
                        "end_position": end_position,
                        "identity_percent": identity_percent,
                        "coverage_percent": coverage_percent,
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

                # Determine resistance class based on Class column
                resistance_class = map_resistance_class(class_name)

                hit = AMRHit(
                    gene_name=gene_symbol or protein_name,
                    gene_family=protein_name,
                    resistance_class=resistance_class,
                    contig_id=sequence_name,
                    start_position=start_position,
                    end_position=end_position,
                    gene_length=abs(end_position - start_position),
                    identity_percent=identity_percent,
                    coverage_percent=coverage_percent,
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
