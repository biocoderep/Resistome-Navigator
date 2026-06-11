import sys
sys.path.append("e:/AMR_platform/AMR_vetgenomehub")
from backend.database.session import SessionLocal
import json
import uuid
import os
from backend.models.amr_gene import AmrGene
from backend.models.virulence_gene import VirulenceGene
from backend.models.resistance_mutation import ResistanceMutation
from backend.models.confidence_score import ConfidenceScore
from backend.models.phenotype_prediction import PhenotypePrediction

db = SessionLocal()
sample_id = "test_uuid"
report_path = "E:/tmp/amr_uploads/test_uuid/results/amr_detection_report.json"

try:
    with open(report_path, "r") as f:
        report = json.load(f)
    
    # Use the rule engine
    from backend.phenotype_engine.rule_repository import RuleRepository
    from backend.phenotype_engine.inference.phenotype_inference import PhenotypeInferenceEngine
    repo = RuleRepository("e:/AMR_platform/AMR_vetgenomehub/backend/phenotype_engine/rules/rule_repository.json")
    engine = PhenotypeInferenceEngine(repo)
    engine.infer_phenotypes(sample_id, report.get("amr_genes", []), report.get("mutations", []), db)

    # Ingest AMR Genes
    for gene in report.get("amr_genes", []):
        db.add(AmrGene(
            id=str(uuid.uuid4()),
            sample_id=sample_id,
            gene_symbol=gene.get("gene_symbol"),
            gene_name=gene.get("gene_name"),
            drug_class=gene.get("drug_class"),
            antibiotic=gene.get("antibiotic"),
            identity=gene.get("identity"),
            coverage=gene.get("coverage"),
            contig_id=gene.get("contig_id"),
            start_pos=gene.get("start_pos"),
            end_pos=gene.get("end_pos"),
            strand=gene.get("strand"),
            evidence_level=gene.get("evidence_level", 1)
        ))

    # Ingest Virulence Genes
    for v in report.get("virulence_genes", []):
        db.add(VirulenceGene(
            id=str(uuid.uuid4()),
            sample_id=sample_id,
            gene_symbol=v.get("gene_symbol"),
            gene_name=v.get("gene_name"),
            virulence_category=v.get("virulence_category"),
            identity=v.get("identity"),
            coverage=v.get("coverage")
        ))

    # Ingest Resistance Mutations
    for m in report.get("mutations", []):
        db.add(ResistanceMutation(
            id=str(uuid.uuid4()),
            sample_id=sample_id,
            gene=m.get("gene"),
            mutation=m.get("mutation"),
            protein_position=m.get("protein_position"),
            ref_amino_acid=m.get("ref_amino_acid"),
            alt_amino_acid=m.get("alt_amino_acid"),
            effect=m.get("effect")
        ))

    # Ingest Confidence Scores
    for c in report.get("confidence_scores", []):
        db.add(ConfidenceScore(
            id=str(uuid.uuid4()),
            sample_id=sample_id,
            finding_type=c.get("finding_type"),
            finding_id=c.get("finding_id"),
            score_dimension=c.get("score_dimension"),
            score=c.get("score")
        ))
    
    db.commit()
    print("Ingestion successful!")
    
    genes = db.query(AmrGene).filter_by(sample_id=sample_id).count()
    muts = db.query(ResistanceMutation).filter_by(sample_id=sample_id).count()
    virs = db.query(VirulenceGene).filter_by(sample_id=sample_id).count()
    phens = db.query(PhenotypePrediction).filter_by(sample_id=sample_id).count()
    
    print(f"Ingested {genes} AMR genes, {muts} mutations, {virs} virulence genes, and {phens} phenotypes.")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
