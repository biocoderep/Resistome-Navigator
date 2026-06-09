"""Module 2 CSV Export engine - Module 1E v1.0.0"""

import csv
from pathlib import Path
from typing import List, Dict, Any
from .result_models import PhenotypePrediction

SCHEMA_VERSION = "1.0.0"

def export_module2_csv(predictions: List[PhenotypePrediction], sample_meta: Dict[str, Any], out_path: Path) -> int:
    """Export predictions to module2_input.csv. Returns row count."""
    rows = []
    for pred in predictions:
        gene_entries = pred.supporting_genes or [""]
        mut_entries = pred.supporting_mutations or [""]
        mech_entries = pred.supporting_mechanisms or [""]
        
        for gene in gene_entries:
            for mutation in mut_entries:
                rows.append({
                    "sample_id": sample_meta.get("sample_id", ""),
                    "isolate_name": sample_meta.get("isolate_name", ""),
                    "species": sample_meta.get("species", ""),
                    "antibiotic": pred.drug,
                    "antibiotic_class": pred.antibiotic_class,
                    "drug_class": pred.drug_class,
                    "predicted_sir": pred.predicted_sir,
                    "confidence_score": pred.confidence_score,
                    "confidence_tier": pred.confidence_tier,
                    "amr_gene": gene,
                    "mutation_notation": mutation,
                    "mechanism_code": ";".join(mech_entries),
                    "supporting_rules": ";".join(pred.supporting_rules),
                    "breakpoint_source": pred.breakpoint_source,
                    "explanation": pred.explanation[:500],
                    "schema_version": SCHEMA_VERSION
                })
                
    if not rows:
        return 0
        
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        
    return len(rows)
