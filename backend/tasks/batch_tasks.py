"""Batch orchestration tasks using Celery Chords.

Single-isolate runs execute the Nextflow ``main.nf`` pipeline, which emits the
canonical ``isolate_report.json`` (see ``backend/pipeline/report_schema.py``).
This module then ingests that report into the normalised ORM tables. Every
finding is tied to an :class:`AnalysisJob` (the required ``job_id`` FK) created
per run, and each report field maps 1:1 onto its model column.
"""

from __future__ import annotations

import datetime as dt
import os
import subprocess
import uuid
from pathlib import Path
from typing import Any, Optional

from celery import chord, group, shared_task
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.session import SessionLocal
from backend.models.amr_gene import AmrGene
from backend.models.analysis_job import AnalysisJob
from backend.models.batch import Batch
from backend.models.confidence_score import ConfidenceScore
from backend.models.phenotype_prediction import PhenotypePrediction
from backend.models.resistance_mutation import ResistanceMutation
from backend.models.sample import Sample
from backend.models.virulence_gene import VirulenceGene

# Where main.nf lives inside the runtime container (matches existing deployment).
NEXTFLOW_MAIN = os.getenv("NEXTFLOW_MAIN", "/app/nextflow/main.nf")
UPLOAD_ROOT = os.getenv("AMR_UPLOAD_ROOT", "/tmp/amr_uploads")


def _num(value: Any) -> Optional[float]:
    """Coerce a numeric-ish value to float, preserving None."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _find_report(out_dir: str, sample_id: str) -> Optional[Path]:
    """Locate the canonical isolate_report.json for a sample."""
    expected = Path(out_dir) / str(sample_id) / "reports" / "isolate_report.json"
    if expected.exists():
        return expected
    # Fallback: search the output tree (handles layout drift).
    matches = list(Path(out_dir).rglob("isolate_report.json"))
    return matches[0] if matches else None


def _ingest_report(
    db: Session, sample_uuid: uuid.UUID, job_uuid: uuid.UUID, report: dict
) -> dict:
    """Persist every section of an isolate report into the ORM tables."""
    counts = {
        "amr_genes": 0,
        "virulence_genes": 0,
        "mutations": 0,
        "confidence_scores": 0,
        "phenotypes": 0,
    }

    for gene in report.get("amr_genes", []):
        db.add(
            AmrGene(
                sample_id=sample_uuid,
                job_id=job_uuid,
                gene_name=gene.get("gene_name"),
                gene_family=gene.get("gene_family"),
                antibiotic_class=gene.get("antibiotic_class") or gene.get("drug_class"),
                resistance_mechanism=gene.get("resistance_mechanism"),
                confidence_score=_num(gene.get("confidence_score")),
            )
        )
        counts["amr_genes"] += 1

    for v in report.get("virulence_genes", []):
        db.add(
            VirulenceGene(
                sample_id=sample_uuid,
                job_id=job_uuid,
                gene_name=v.get("gene_name"),
                virulence_factor=v.get("virulence_factor") or v.get("virulence_category"),
                mechanism=v.get("mechanism"),
                contig_id=v.get("contig_id"),
                start_position=v.get("start_position"),
                end_position=v.get("end_position"),
                identity_percent=_num(v.get("identity_percent")),
                coverage_percent=_num(v.get("coverage_percent")),
                database_source=v.get("database_source"),
            )
        )
        counts["virulence_genes"] += 1

    for m in report.get("mutations", []):
        db.add(
            ResistanceMutation(
                sample_id=sample_uuid,
                job_id=job_uuid,
                gene_name=m.get("gene_name"),
                mutation=m.get("mutation"),
                mechanism=m.get("mechanism"),
                effect=m.get("effect"),
                identity_percent=_num(m.get("identity_percent")),
                coverage_percent=_num(m.get("coverage_percent")),
                database_source=m.get("database_source"),
            )
        )
        counts["mutations"] += 1

    for c in report.get("confidence_scores", []):
        db.add(
            ConfidenceScore(
                sample_id=sample_uuid,
                job_id=job_uuid,
                context=c.get("context", "amr_gene"),
                target_name=c.get("target_name", "unknown"),
                overall_score=_num(c.get("overall_score")) or 0.0,
                tier=c.get("tier", "LOW"),
                cap_applied=bool(c.get("cap_applied", False)),
                components=c.get("components", {}) or {},
                weighted=c.get("weighted", {}) or {},
            )
        )
        counts["confidence_scores"] += 1

    for p in report.get("phenotypes", []):
        db.add(
            PhenotypePrediction(
                sample_id=sample_uuid,
                job_id=job_uuid,
                drug=p.get("drug"),
                drug_class=p.get("drug_class"),
                predicted_sir=p.get("predicted_sir", "U"),
                confidence_score=_num(p.get("confidence_score")),
                confidence_tier=p.get("confidence_tier"),
                breakpoint_source=p.get("breakpoint_source"),
                breakpoint_version=p.get("breakpoint_version"),
                is_not_testable=bool(p.get("is_not_testable", False)),
                has_conflict=bool(p.get("has_conflict", False)),
                supporting_genes=p.get("supporting_genes", []) or [],
                supporting_mutations=p.get("supporting_mutations", []) or [],
                explanation=p.get("explanation"),
            )
        )
        counts["phenotypes"] += 1

    db.commit()
    return counts


@shared_task(bind=True)
def dispatch_batch_workflow(self, batch_id: str, sample_ids: list[str], run_cohort: bool):
    """Entry point for orchestrating a batch run."""
    db = SessionLocal()
    try:
        batch = db.scalars(select(Batch).where(Batch.id == uuid.UUID(batch_id))).first()
        if batch:
            batch.status = "RUNNING"
            db.commit()
    finally:
        db.close()

    tasks = [run_single_isolate_pipeline.s(sample_id) for sample_id in sample_ids]

    if run_cohort:
        chord(tasks)(run_cohort_analysis.s(batch_id=batch_id))
    else:
        group(tasks).apply_async()

    return "DISPATCHED"


@shared_task(bind=True)
def run_single_isolate_pipeline(self, sample_id: str):
    """Run the Nextflow pipeline for one isolate and ingest its report."""
    db = SessionLocal()
    sample = None
    job: Optional[AnalysisJob] = None
    sample_uuid = uuid.UUID(str(sample_id))
    try:
        sample = db.scalars(select(Sample).where(Sample.id == sample_uuid)).first()
        if not sample:
            raise ValueError(f"sample {sample_id} not found")
        sample.status = "RUNNING"

        # Track this run with an AnalysisJob (provides the required job_id FK).
        job = AnalysisJob(
            sample_id=sample_uuid,
            job_type="MODULE1_AMR",
            status="RUNNING",
            started_at=dt.datetime.now(dt.timezone.utc),
        )
        db.add(job)
        db.commit()
        job_uuid = job.id

        # Resolve the assembly FASTA for this sample.
        file_path = None
        for f in sample.files:
            if f.file_type == "assembly_fasta":
                file_path = f.file_path
                break
        if not file_path or not os.path.exists(file_path):
            raise FileNotFoundError("Assembly FASTA file not found.")

        # Stage a single-row samples.csv (the same per-sample channel the batch
        # path uses, so single and batch share one code path).
        isolate_dir = os.path.join(UPLOAD_ROOT, str(sample_id))
        os.makedirs(isolate_dir, exist_ok=True)
        csv_path = os.path.join(isolate_dir, "samples.csv")
        out_dir = os.path.join(isolate_dir, "results")
        species = sample.species or "Unknown"

        with open(csv_path, "w") as f:
            f.write("sample_id,assembly_file,species\n")
            f.write(f"{sample_id},{file_path},{species}\n")

        proc = subprocess.run(
            [
                "nextflow", "run", NEXTFLOW_MAIN,
                "--samples", csv_path,
                "--output", out_dir,
                "-profile", "local",
            ],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"Nextflow failed: {proc.stderr[-2000:]}")

        report_path = _find_report(out_dir, sample_id)
        if not report_path:
            raise FileNotFoundError(
                f"isolate_report.json not produced under {out_dir}"
            )

        import json

        report = json.loads(report_path.read_text(encoding="utf-8"))
        counts = _ingest_report(db, sample_uuid, job_uuid, report)

        job.status = "COMPLETED"
        job.completed_at = dt.datetime.now(dt.timezone.utc)
        sample.status = "COMPLETED"
        db.commit()

        # Update batch progress.
        if sample.batch_id:
            batch = db.scalars(
                select(Batch).where(Batch.id == uuid.UUID(str(sample.batch_id)))
            ).first()
            if batch:
                batch.completed_isolates = (batch.completed_isolates or 0) + 1
                db.commit()

        return {"sample_id": sample_id, "status": "success", "ingested": counts}

    except Exception as e:  # noqa: BLE001 - record failure, keep cohort alive
        db.rollback()
        if job is not None:
            job.status = "FAILED"
            job.completed_at = dt.datetime.now(dt.timezone.utc)
        if sample is not None:
            sample.status = "FAILED"
        db.commit()
        if sample is not None and sample.batch_id:
            batch = db.scalars(
                select(Batch).where(Batch.id == uuid.UUID(str(sample.batch_id)))
            ).first()
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
    batch = None
    try:
        batch = db.scalars(select(Batch).where(Batch.id == uuid.UUID(batch_id))).first()
        if batch:
            batch.status = "ISOLATES_COMPLETE"
            batch.cohort_analysis_status = "RUNNING"
            db.commit()

        successful_samples = [r["sample_id"] for r in results if r["status"] == "success"]

        if len(successful_samples) < 3:
            if batch:
                batch.cohort_analysis_status = "SKIPPED_INSUFFICIENT_ISOLATES"
                batch.status = "COMPLETED"
                db.commit()
            return {"batch_id": batch_id, "status": "skipped"}

        from backend.cohort_engine.analyzer import run_full_cohort_analysis

        run_full_cohort_analysis(batch_id, successful_samples, db)

        if batch:
            batch.cohort_analysis_status = "COMPLETED"
            batch.status = "COMPLETED"
            db.commit()

        return {"batch_id": batch_id, "status": "completed"}
    except Exception as e:  # noqa: BLE001
        if batch:
            batch.cohort_analysis_status = "FAILED"
            batch.status = "COMPLETED"
            db.commit()
        raise e
    finally:
        db.close()
