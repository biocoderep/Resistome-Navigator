"""Demo script to verify the Phenotype Prediction Engine."""

import sys
from pathlib import Path

# Ensure the root directory is in sys.path so 'backend' can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.phenotype_engine.rule_repository import RuleRepository
from backend.phenotype_engine.breakpoints.eucast_adapter import EUCASTAdapter
from backend.phenotype_engine.inference.confidence_propagation import ConfidencePropagator
from backend.phenotype_engine.inference.phenotype_inference import PhenotypeInferenceEngine
from backend.phenotype_engine.result_models import AMRGeneResult
from backend.phenotype_engine.module2_export import export_module2_csv

# We need some stub objects to mock the output of the Mutation Mechanism Engine
class MockMutation:
    def __init__(self, gene_name, notation, clss, confidence):
        self.gene_name = gene_name
        self.mutation_notation = notation
        self.classification = clss
        self.confidence_score = confidence

class MockMechanism:
    def __init__(self, code, name, drug_classes, confidence):
        self.mechanism_code = code
        self.mechanism_name = name
        self.drug_classes = drug_classes
        self.confidence = confidence

def main():
    print("=== Testing Phenotype Prediction Engine ===")
    
    repo_path = Path("backend/phenotype_engine/rules/rule_repository.json")
    print("[1] Loading Rule Repository...")
    rule_repo = RuleRepository(repo_path)
    
    print("[2] Initializing Breakpoint Adapters and Propagators...")
    bp_adapter = EUCASTAdapter()
    conf_prop = ConfidencePropagator()
    
    engine = PhenotypeInferenceEngine(rule_repo, bp_adapter, conf_prop)
    
    print("[3] Creating Mock Evidence...")
    # Mocking a CTX-M-15 gene (triggers gene rule)
    genes = [
        AMRGeneResult(gene_name="blaCTX-M-15", gene_family="CTX-M beta-lactamase", aro_accession="ARO:1000001",
                      hit_type="Perfect", identity_pct=100.0, coverage_pct=100.0, confidence_score=0.99)
    ]
    
    # Mocking a gyrA mutation and parC mutation (triggers combinatorial rule)
    mutations = [
        MockMutation("gyrA", "S83L", "KNOWN_RESISTANCE", 0.95),
        MockMutation("parC", "S80I (Domain: QRDR)", "KNOWN_RESISTANCE", 0.90)
    ]
    
    # Mocking an efflux pump
    mechanisms = [
        MockMechanism("efflux_pump", "Tet Efflux", ["tetracycline"], 0.85)
    ]
    
    print("[4] Running Phenotype Inference...")
    predictions = engine.predict(
        sample_id="SAMPLE_001",
        assembly_quality="FULL",
        genes=genes,
        mutations=mutations,
        mechanisms=mechanisms,
        species="Klebsiella pneumoniae"
    )
    
    print("\n--- Final Predictions ---")
    for p in predictions:
        print(f"\n{p.explanation}")
        
    print("\n[5] Exporting Module 2 Data...")
    export_path = Path("module2_input.csv")
    rows = export_module2_csv(predictions, {"sample_id": "SAMPLE_001", "isolate_name": "ISOLATE_X", "species": "Klebsiella pneumoniae"}, export_path)
    print(f"Exported {rows} rows to {export_path}")

if __name__ == "__main__":
    main()
