"""Report generation engine - Module 1D v1.0.0"""

import json
from pathlib import Path
from typing import Dict, Any

from .result_models import MutationDetectionResult

class ReportGenerator:
    """Generate JSON/TSV reports for mutation and mechanism analysis."""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_mutation_json(self, result: MutationDetectionResult):
        """Generate mutations JSON report."""
        out_file = self.output_dir / "resistance_mutations.json"
        
        data = {
            "sample_id": str(result.sample_id),
            "job_id": str(result.job_id),
            "total_mutations": result.total_mutations,
            "mutations": [
                {
                    "gene": v.raw_variant.gene_name,
                    "notation": v.mutation_notation,
                    "hgvs_p": v.hgvs_protein,
                    "hgvs_c": v.hgvs_cdna,
                    "effect": v.effect.value,
                    "domain": v.domain
                }
                for v in result.mutations
            ]
        }
        
        with open(out_file, "w") as f:
            json.dump(data, f, indent=2)
            
        return out_file

    def generate_novel_mutation_json(self, novel_data: Dict[str, Any]):
        """Generate novel mutations JSON report."""
        out_file = self.output_dir / "novel_mutation_report.json"
        
        with open(out_file, "w") as f:
            json.dump(novel_data, f, indent=2)
            
        return out_file
