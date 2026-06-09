"""Demo script to verify the Virulence Profiling and Confidence Scoring Engine."""

import sys
from pathlib import Path
import uuid

# Ensure the root directory is in sys.path so 'backend' can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.virulence_engine.result_models import VirulenceFactor
from backend.virulence_engine.adapters.vfdb_adapter import VFDBAdapter
from backend.virulence_engine.adapters.virulencefinder_adapter import VirulenceFinderAdapter
from backend.virulence_engine.virulence_classifier import VirulenceClassifier
from backend.virulence_engine.pathogenicity_profile import compute_pathogenicity_profile
from backend.amr_confidence.confidence_aggregation import aggregate
from backend.amr_confidence.confidence_explanation import explain_confidence

def main():
    print("=== Testing Virulence Profiling & Confidence Scoring Engine ===")
    
    # 1. Initialize DB adapters (using stubs)
    print("\n[1] Running Virulence Scanners...")
    vfdb = VFDBAdapter(db_version_id="2024.1")
    vf_finder = VirulenceFinderAdapter(db_version_id="2.0.3")
    
    dummy_fasta = Path("dummy.fasta")
    raw_hits = vfdb.run(dummy_fasta) + vf_finder.run(dummy_fasta)
    print(f"Detected {len(raw_hits)} raw hits.")
    
    # 2. Ontology & Classification
    print("\n[2] Classifying Hits & Applying Ontology...")
    ontology_path = Path(__file__).parent / "virulence_engine" / "ontology" / "virulence_ontology.json"
    gene_map_path = Path(__file__).parent / "virulence_engine" / "ontology" / "gene_category_map.json"
    
    classifier = VirulenceClassifier(ontology_path, gene_map_path)
    
    factors = []
    for hit in raw_hits:
        cls_data = classifier.classify(hit)
        
        # 3. Confidence Scoring
        conf_result = aggregate(
            identity_pct=hit.identity_pct,
            coverage_pct=hit.coverage_pct,
            bit_score=hit.bit_score,
            e_value=hit.e_value,
            supporting_tools=[hit.tool], # Mocking tool agreement
            evidence_types=["computational"],
            context="virulence",
            genome_quality="FULL",
            reference_length=1000
        )
        
        factor = VirulenceFactor(
            vf_id=str(uuid.uuid4()),
            sample_id="SAMPLE_O157",
            gene_name=hit.gene_name,
            category_code=cls_data["category_code"],
            category_display=cls_data["category_display"],
            function_description=hit.vf_function,
            detection_tool=hit.tool,
            db_version_id=hit.db_version_id,
            identity_pct=hit.identity_pct,
            coverage_pct=hit.coverage_pct,
            bit_score=hit.bit_score,
            e_value=hit.e_value,
            contig_id=hit.contig_id,
            start=hit.start,
            end=hit.end,
            strand=hit.strand,
            is_high_risk=cls_data["is_high_risk"],
            risk_weight=cls_data["risk_weight"],
            confidence=conf_result,
            vfdb_id=None
        )
        factors.append(factor)
        
        # Print Confidence Explanations
        print(f"\n--- {factor.gene_name} ({factor.category_display}) ---")
        print(f"High Risk: {factor.is_high_risk}")
        print(explain_confidence(factor.confidence, factor.gene_name))

    # 4. Pathogenicity Profiling
    print("\n[3] Computing Pathogenicity Risk Profile...")
    profile = compute_pathogenicity_profile("SAMPLE_O157", factors)
    
    print("\n--- FINAL PATHOGENICITY PROFILE ---")
    print(f"Sample: {profile.sample_id}")
    print(f"Total VF Genes: {profile.total_vf_genes}")
    print(f"Category Diversity: {profile.category_diversity}")
    print(f"High Risk Genes Detected: {', '.join(profile.high_risk_genes)}")
    print(f"RISK SCORE: {profile.risk_score}/100")
    print(f"RISK CLASS: {profile.risk_class}")

if __name__ == "__main__":
    main()
