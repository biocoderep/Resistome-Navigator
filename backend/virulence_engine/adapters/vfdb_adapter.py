"""VFDB virulence factor adapter for ABRICATE TSV output."""

import re
from pathlib import Path
from typing import List
from ..result_models import VirulenceRawHit

class VFDBAdapter:
    def __init__(self, db_version_id: str = "2024.1"):
        self.db_version_id = db_version_id

    def parse_results(self, tsv_file: Path) -> List[VirulenceRawHit]:
        """Parse ABRICATE TSV output format."""
        hits = []

        if not tsv_file.exists():
            return []

        try:
            with open(tsv_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if not lines:
                return []

            header = lines[0].strip().split("\t")
            header_map = {name: idx for idx, name in enumerate(header)}

            for line in lines[1:]:
                fields = line.strip().split("\t")
                if len(fields) < len(header):
                    continue

                # Standard ABRICATE columns: FILE, SEQUENCE, START, END, STRAND, GENE, COVERAGE, COVERAGE_MAP, GAPS, %COVERAGE, %IDENTITY, DATABASE, ACCESSION, PRODUCT, RESISTANCE
                contig_id = fields[header_map.get("SEQUENCE", 1)] if "SEQUENCE" in header_map else ""
                start = int(fields[header_map.get("START", 2)]) if "START" in header_map else 0
                end = int(fields[header_map.get("END", 3)]) if "END" in header_map else 0
                strand = fields[header_map.get("STRAND", 4)] if "STRAND" in header_map else "+"
                gene_name = fields[header_map.get("GENE", 5)] if "GENE" in header_map else ""
                coverage_pct = float(fields[header_map.get("%COVERAGE", 9)]) if "%COVERAGE" in header_map else 100.0
                identity_pct = float(fields[header_map.get("%IDENTITY", 10)]) if "%IDENTITY" in header_map else 100.0
                product = fields[header_map.get("PRODUCT", 13)] if "PRODUCT" in header_map else ""

                hits.append(VirulenceRawHit(
                    tool="ABRICATE-VFDB",
                    gene_name=gene_name,
                    identity_pct=identity_pct,
                    coverage_pct=coverage_pct,
                    db_version_id=self.db_version_id,
                    vf_function=product,
                    contig_id=contig_id,
                    start=start,
                    end=end,
                    bit_score=0.0, # Not in abricate usually
                    e_value=0.0,   # Not in abricate usually
                    strand=strand
                ))

        except Exception as e:
            # We fail gracefully and return whatever we successfully parsed (usually [])
            pass

        return hits
