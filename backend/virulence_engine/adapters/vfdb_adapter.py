"""VFDB virulence factor adapter - Module 1F v1.0.0"""

import re
from pathlib import Path
from typing import List
from ..result_models import VirulenceRawHit

class VFDBAdapter:
    def __init__(self, db_version_id: str):
        self.db_version_id = db_version_id
        # VFDB sequence header format: >VF####(GB|VF_XXXXXX) [gene_name] [function] [organism]
        self.vfdb_header_re = re.compile(
            r"VF(?P<vf_id>\d+).*?\[(?P<gene>[^\]]+)\]\s*\[(?P<function>[^\]]+)\]"
        )

    def run(self, fasta: Path, min_identity: float = 75.0, min_coverage: float = 60.0) -> List[VirulenceRawHit]:
        """Stub method for demonstration.
        Normally this would execute 'blastn' against the VFDB database."""
        # For demonstration purposes, we will return some mock hits if the fasta is the mock one
        return [
            VirulenceRawHit(
                tool="VFDB", gene_name="stx1", vf_category="toxin", vf_function="Shiga toxin 1",
                identity_pct=100.0, coverage_pct=100.0, contig_id="contig_1", start=100, end=1000,
                bit_score=1500.0, e_value=0.0, db_version_id=self.db_version_id
            ),
            VirulenceRawHit(
                tool="VFDB", gene_name="fimH", vf_category="adhesin", vf_function="Type 1 fimbrial adhesin",
                identity_pct=98.5, coverage_pct=95.0, contig_id="contig_2", start=500, end=1200,
                bit_score=800.0, e_value=1e-150, db_version_id=self.db_version_id
            )
        ]

    def _parse_vfdb_header(self, header: str):
        m = self.vfdb_header_re.search(header)
        if m:
            return m.group("gene"), "unknown", m.group("function")
        return "unknown", "unknown", "unknown"
