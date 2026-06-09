import sys
import uuid
import json
from pathlib import Path

# Add project root directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.mutation_engine.mutation_detection_engine import MutationDetectionEngine
from backend.mutation_engine.mechanism_classification_engine import MechanismClassificationEngine
from backend.mutation_engine.result_models import MutationMapping, MutationClassification

def main():
    print("=== Testing Mutation & Mechanism Engine ===")
    
    # 1. Create a mock FASTA
    fasta_path = Path("mock_genome.fasta")
    # A short sequence that contains "ATGCGT" (the mock reference for gyrA in the engine)
    fasta_path.write_text(">contig_1\nATGCGTACGTTAGC\n>contig_2\nATGGCTC\n")

    # 2. Run Mutation Detection
    print("\n--- Phase 1: Mutation Detection ---")
    detector = MutationDetectionEngine(job_id="job-123", config={"sample_id": str(uuid.uuid4())})
    
    def print_progress(progress, step):
        print(f"[{progress:>3}%] {step}")
        
    result = detector.run(str(fasta_path), species="Escherichia coli", progress_cb=print_progress)
    
    print(f"\nFound {result.total_mutations} variants in mock genome.")
    for variant in result.mutations:
        print(f" -> {variant.mutation_notation} (Effect: {variant.effect.value}, Domain: {variant.domain})")

    # 3. Setup Mechanism Classification
    print("\n--- Phase 2: Mechanism Classification ---")
    
    # Create a mock ontology file
    ontology_path = Path("mock_ontology.json")
    ontology_path.write_text(json.dumps({
        "mechanism_classes": [
            {"code": "target_alteration", "display_name": "Target Site Alteration", "drug_classes": ["fluoroquinolone"]},
            {"code": "efflux_pump", "display_name": "Efflux Pump Overexpression", "drug_classes": ["tetracycline"]}
        ]
    }))

    class MockAroMapper:
        def lookup(self, aro): return {"resistance_mechanism": "target_alteration"}

    mock_kb = [
        {"entry_id": "M1", "gene": "gyrA", "protein_position": 1, "alt_amino_acid": "M", "mechanism": "target_alteration", "evidence_level": 1}
    ]

    classifier = MechanismClassificationEngine(
        job_id="job-123",
        config={},
        ontology_path=ontology_path,
        aro_mapper=MockAroMapper(),
        kb=mock_kb
    )
    
    # Create mock mappings for our found mutations
    mappings = [MutationMapping(classification=MutationClassification.NOVEL)] * len(result.mutations)
    
    mech_result = classifier.run(
        genes=[], # No acquired genes for this test
        mutations=result.mutations, 
        mappings=mappings,
        progress_cb=print_progress
    )

    print("\n--- Results ---")
    print("\nMechanisms Identified:")
    for mech in mech_result["mechanisms"]:
        print(f" -> {mech.mechanism_name}")
        print(f"    Drugs Affected: {mech.drug_classes}")
        print(f"    Supported by mutations: {mech.supporting_mutations}")

    print("\nDrug Associations (Phenotype Predictions):")
    for drug in mech_result["drug_associations"]:
        print(f" -> {drug.drug_name} ({drug.drug_class}): Predicted {drug.sir_prediction.value}")
        
    # Cleanup mock files
    fasta_path.unlink()
    ontology_path.unlink()

if __name__ == "__main__":
    main()
