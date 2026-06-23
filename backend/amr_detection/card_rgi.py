"""CARD RGI AMR detection wrapper."""

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


class CARDRGIDetector(BaseAMRDetector):
    """CARD RGI-based AMR detection tool."""

    def __init__(self, config: Optional[AMRConfig] = None):
        """Initialize CARD RGI detector."""
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
        Execute CARD RGI AMR detection.

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
            progress_callback(10, "Initializing CARD RGI")

        output_dir.mkdir(parents=True, exist_ok=True)
        output_prefix = output_dir / "rgi"

        result = AMRDetectionResult(
            detection_id=uuid4(),
            sample_id=sample_id or uuid4(),
            assembly_id=assembly_id or uuid4(),
            tools_run=["card_rgi"],
            total_amr_genes=0,
            unique_gene_families=0,
            resistance_classes=[],
        )

        try:
            # Build RGI command
            cmd = [
                "rgi",
                "main",
                "-i",
                str(assembly_file),
                "-o",
                str(output_prefix),
                "-t",
                "contig",
                "-a",
                "BLAST",
                "-n",
                str(self.config.threads),
            ]

            if progress_callback:
                progress_callback(20, "Running CARD RGI analysis")

            # Execute RGI
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600,
            )

            if process.returncode != 0:
                result.errors.append(f"RGI failed: {process.stderr}")
                return result

            if progress_callback:
                progress_callback(50, "Parsing RGI results")

            # Parse JSON results
            json_output = output_prefix.with_suffix(".json")
            if json_output.exists():
                hits, mutation_hits = self._parse_rgi_json(json_output)
                result.hits = hits
                result.mutation_hits = mutation_hits

                if progress_callback:
                    progress_callback(80, "Computing AMR statistics")

                # Compute statistics
                result.total_amr_genes = len(hits)
                result.unique_gene_families = len(set(h.gene_family for h in hits))
                result.resistance_classes = list(
                    set(h.resistance_class for h in hits)
                )

                # Compute phenotype summary
                phenotype_map = {}
                for hit in hits:
                    if hit.phenotype:
                        phenotype_map[hit.phenotype] = (
                            phenotype_map.get(hit.phenotype, 0) + 1
                        )
                result.phenotype_summary = phenotype_map

            result.output_files["rgi_json"] = str(json_output)
            result.output_files["rgi_txt"] = str(output_prefix.with_suffix(".txt"))

            if progress_callback:
                progress_callback(100, "CARD RGI analysis complete")

        except subprocess.TimeoutExpired:
            result.errors.append("CARD RGI analysis timed out after 1 hour")
        except Exception as e:
            result.errors.append(f"Analysis error: {str(e)}")

        return result

    def _parse_rgi_json(self, json_file: Path) -> tuple[list[AMRHit], list[dict]]:
        """Parse RGI JSON output."""
        hits = []
        mutation_hits = []

        try:
            with open(json_file) as f:
                data = json.load(f)

            # RGI output format: {"ORF#": {"Blast_Hit_ID": {...}}}
            for orf_id, orf_hits in data.items():
                if not isinstance(orf_hits, dict):
                    continue
                
                best_hit = None
                best_score = -1.0
                best_type_rank = -1
                
                for _k, hit in orf_hits.items():
                    if not isinstance(hit, dict):
                        continue
                        
                    hittype = hit.get("type_match", "")
                    if hittype not in ("Perfect", "Strict"):
                        continue
                        
                    type_rank = 2 if hittype == "Perfect" else 1
                    try:
                        score = float(hit.get("pass_bitscore", 0.0))
                    except ValueError:
                        score = 0.0
                        
                    if type_rank > best_type_rank or (type_rank == best_type_rank and score > best_score):
                        best_type_rank = type_rank
                        best_score = score
                        best_hit = hit

                if not best_hit:
                    continue
                
                hit = best_hit
                
                gene_name = hit.get("ARO_name", "Unknown")
                
                # Parse ARO_category for gene_family and drug_class
                aro_category = hit.get("ARO_category", {})
                gene_family = "Unknown"
                drug_class = ""
                
                if isinstance(aro_category, dict):
                    drug_classes = []
                    for cat_id, cat_info in aro_category.items():
                        if not isinstance(cat_info, dict):
                            continue
                        cat_name = cat_info.get("category_aro_name", "")
                        cat_class = cat_info.get("category_aro_class_name", "")
                        if cat_class == "AMR Gene Family":
                            gene_family = cat_name
                        elif cat_class == "Drug Class":
                            drug_classes.append(cat_name)
                    
                    if drug_classes:
                        drug_class = ", ".join(drug_classes)
                        
                if not drug_class:
                    drug_class = gene_family
                
                contig = hit.get("orf_from", "Unknown")
                start = int(hit.get("orf_start", 0))
                stop = int(hit.get("orf_end", 0))
                identity = float(hit.get("perc_identity", 0.0))
                coverage = float(hit.get("query_coverage", 0.0))
                model_type = hit.get("model_type", "")
                snps = hit.get("snps_in_isolate", [])

                if model_type == "protein variant model" or "Variant" in model_type:
                    # RGI SNP format: {"original": "S", "mutation": "L", "position": 83}
                    for snp in snps:
                        orig = snp.get("original", "")
                        mut = snp.get("mutation", "")
                        pos = snp.get("position", "")
                        mutation_str = f"{orig}{pos}{mut}" if orig and mut and pos else str(snp)
                        
                        mutation_hits.append({
                            "gene_name": gene_name,
                            "mutation": mutation_str,
                            "mechanism": "Point Mutation",
                            "effect": "Missense",
                            "identity_percent": identity,
                            "coverage_percent": coverage,
                            "database_source": "CARD"
                        })
                    
                    # We might still want to add the hit itself to AMR genes or just mutations
                    # Given the contract, mutations are separate, so we can skip adding to hits
                    continue

                # Determine confidence
                if identity >= 99.0:
                    confidence = ConfidenceLevel.HIGH
                elif identity >= 95.0:
                    confidence = ConfidenceLevel.MEDIUM
                else:
                    confidence = ConfidenceLevel.LOW

                # Determine resistance class
                resistance_class = map_resistance_class(drug_class)

                amr_hit = AMRHit(
                    gene_name=gene_name,
                    gene_family=gene_family,
                    resistance_class=resistance_class,
                    contig_id=contig,
                    start_position=min(start, stop),
                    end_position=max(start, stop),
                    gene_length=abs(stop - start),
                    identity_percent=identity,
                    coverage_percent=coverage,
                    tool_name="card_rgi",
                    confidence=confidence,
                    phenotype=hit.get("phenotype", None),
                )
                hits.append(amr_hit)

        except Exception as e:
            return [], []

        return hits, mutation_hits

    def parse_results(self, output_dir: Path) -> tuple[list[AMRHit], list[dict]]:
        """Parse RGI results."""
        json_file = output_dir / "rgi.json"
        if json_file.exists():
            return self._parse_rgi_json(json_file)
        return [], []
