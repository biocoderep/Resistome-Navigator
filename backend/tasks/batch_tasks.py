"""Batch orchestration tasks using Celery Chords."""

from celery import shared_task, chord, group
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.database.session import SessionLocal
from backend.models.batch import Batch
from backend.models.sample import Sample
import subprocess
import os

@shared_task(bind=True)
def dispatch_batch_workflow(self, batch_id: str, sample_ids: list[str], run_cohort: bool):
    """Entry point for orchestrating a batch run."""
    db = SessionLocal()
    import uuid
    try:
        batch = db.scalars(select(Batch).where(Batch.id == uuid.UUID(batch_id))).first()
        if batch:
            batch.status = "RUNNING"
            db.commit()
    finally:
        db.close()

    tasks = [run_single_isolate_pipeline.s(sample_id) for sample_id in sample_ids]

    if run_cohort:
        workflow = chord(tasks)(run_cohort_analysis.s(batch_id=batch_id))
    else:
        workflow = group(tasks).apply_async()
        
    return "DISPATCHED"

@shared_task(bind=True)
def run_single_isolate_pipeline(self, sample_id: str):
    """Runs the Nextflow MODULE1_AMR pipeline for a single isolate."""
    db = SessionLocal()
    import uuid
    sample = None
    try:
        sample = db.scalars(select(Sample).where(Sample.id == uuid.UUID(sample_id))).first()
        if sample:
            sample.status = "RUNNING"
            db.commit()
            
        file_path = None
        for file in sample.files:
            if file.file_type == "assembly_fasta":
                file_path = file.file_path
                break
                
        if not file_path or not os.path.exists(file_path):
            raise Exception("Assembly FASTA file not found.")

        # Create isolate-specific directory
        isolate_dir = f"/tmp/amr_uploads/{sample_id}"
        os.makedirs(isolate_dir, exist_ok=True)
        csv_path = os.path.join(isolate_dir, "samples.csv")
        out_dir = os.path.join(isolate_dir, "results")
        
        with open(csv_path, "w") as f:
            f.write("sample_id,assembly_file,species\n")
            f.write(f"{sample_id},{file_path},Unknown\n")
            
        # Run Nextflow
        cmd = [
            "nextflow", "run", "/app/nextflow/main.nf",
            "--samples", csv_path,
            "--output", out_dir,
            "-profile", "local"
        ]
        
        proc = subprocess.run(cmd, capture_output=True, text=True)
        
        if proc.returncode != 0:
            raise Exception(f"Nextflow failed: {proc.stderr}")
            
        # Parse the JSON report produced by Nextflow
        report_path = os.path.join(out_dir, "amr_detection_report.json")
        if os.path.exists(report_path):
            import json
            with open(report_path, "r") as f:
                report = json.load(f)
            
            # Use the rule engine
            from backend.phenotype_engine.rule_repository import RuleRepository
            from backend.phenotype_engine.inference.phenotype_inference import PhenotypeInferenceEngine
            repo = RuleRepository("/app/backend/phenotype_engine/rules/rule_repository.json")
            engine = PhenotypeInferenceEngine(repo)
            engine.infer_phenotypes(sample_id, report.get("amr_genes", []), report.get("mutations", []), db)

            from backend.models.amr_gene import AmrGene
            from backend.models.virulence_gene import VirulenceGene
            from backend.models.resistance_mutation import ResistanceMutation
            from backend.models.confidence_score import ConfidenceScore
            import uuid

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

        if sample:
            sample.status = "COMPLETED"
            db.commit()
            
            # Update batch progress
            if sample.batch_id:
                batch = db.scalars(select(Batch).where(Batch.id == uuid.UUID(str(sample.batch_id)))).first()
                if batch:
                    batch.completed_isolates = (batch.completed_isolates or 0) + 1
                    db.commit()

        return {"sample_id": sample_id, "status": "success"}
    except Exception as e:
        if sample:
            sample.status = "FAILED"
            db.commit()
            if sample.batch_id:
                batch = db.scalars(select(Batch).where(Batch.id == uuid.UUID(str(sample.batch_id)))).first()
                if batch:
                    batch.failed_isolates = (batch.failed_isolates or 0) + 1
                    db.commit()
        return {"sample_id": sample_id, "status": "error", "error": str(e)}
    finally:
        db.close()

@shared_task(bind=True)
def run_cohort_analysis(self, results, batch_id: str):
    """Callback triggered after all isolate pipelines finish."""
    db = SessionLocal()
    import uuid
    batch = None
    try:
        batch = db.scalars(select(Batch).where(Batch.id == uuid.UUID(batch_id))).first()
        if batch:
            batch.status = "ISOLATES_COMPLETE"
            batch.cohort_analysis_status = "RUNNING"
            db.commit()
            
        # Extract sample_ids from successful results
        successful_samples = [r["sample_id"] for r in results if r["status"] == "success"]
        
        if len(successful_samples) < 3:
            if batch:
                batch.cohort_analysis_status = "SKIPPED_INSUFFICIENT_ISOLATES"
                batch.status = "COMPLETED"
                db.commit()
            return {"batch_id": batch_id, "status": "skipped"}
            
        # We need to run the python service for cohort analysis
        from backend.cohort_engine.analyzer import run_full_cohort_analysis
        
        analysis_status = run_full_cohort_analysis(batch_id, successful_samples, db)
        
        if batch:
            batch.cohort_analysis_status = "COMPLETED"
            batch.status = "COMPLETED"
            db.commit()
            
        return {"batch_id": batch_id, "status": "completed"}
    except Exception as e:
        if batch:
            batch.cohort_analysis_status = "FAILED"
            batch.status = "COMPLETED"
            db.commit()
        raise e
    finally:
        db.close()
