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
    try:
        batch = db.scalars(select(Batch).where(Batch.id == batch_id)).first()
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
    try:
        sample = db.scalars(select(Sample).where(Sample.id == sample_id)).first()
        if sample:
            sample.status = "RUNNING"
            db.commit()
        
        # Simulate or call actual Nextflow pipeline
        # For MVP, we simulate a successful run taking a few seconds.
        import time
        time.sleep(2)

        if sample:
            sample.status = "COMPLETED"
            db.commit()
            
            # Update batch progress
            if sample.batch_id:
                batch = db.scalars(select(Batch).where(Batch.id == sample.batch_id)).first()
                if batch:
                    batch.completed_isolates = (batch.completed_isolates or 0) + 1
                    db.commit()

        return {"sample_id": sample_id, "status": "success"}
    except Exception as e:
        if sample:
            sample.status = "FAILED"
            db.commit()
            if sample.batch_id:
                batch = db.scalars(select(Batch).where(Batch.id == sample.batch_id)).first()
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
    try:
        batch = db.scalars(select(Batch).where(Batch.id == batch_id)).first()
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
