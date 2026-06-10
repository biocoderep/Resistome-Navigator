"""Batch and Cohort processing routes."""

import hashlib
import os
import asyncio
from datetime import datetime
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
    WebSocket,
    WebSocketDisconnect,
    BackgroundTasks
)
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.database.session import get_session
from backend.models.batch import Batch, CohortResult
from backend.models.sample import Sample
from backend.models.sample_file import SampleFile
from backend.schemas.batch import BatchResponse, BatchIsolateStatus, CohortAnalysisResponse
from backend.tasks.batch_tasks import dispatch_batch_workflow

router = APIRouter(prefix="/batches", tags=["batches"])
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/amr_uploads")
ALLOWED_EXTENSIONS = (".fasta", ".fa", ".fna", ".fasta.gz", ".fa.gz")

@router.post("", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
def upload_batch(
    background_tasks: BackgroundTasks,
    project_id: UUID = Form(...),
    batch_name: str | None = Form(default=None),
    run_cohort_analysis: bool = Form(default=True),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_session)
):
    """Upload multiple fasta files as a single batch."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    batch = Batch(
        project_id=str(project_id),
        batch_name=batch_name,
        run_cohort_analysis=run_cohort_analysis,
        total_isolates=len(files),
        status="DISPATCHING"
    )
    db.add(batch)
    db.flush()

    sample_ids = []
    isolate_statuses = []

    for file in files:
        if not file.filename.lower().endswith(ALLOWED_EXTENSIONS):
            continue

        sample = Sample(
            batch_id=batch.id,
            project_id=str(project_id),
            isolate_name=file.filename,
            status="QUEUED"
        )
        db.add(sample)
        db.flush()

        sample_dir = os.path.join(UPLOAD_DIR, str(sample.id))
        os.makedirs(sample_dir, exist_ok=True)
        dest_path = os.path.join(sample_dir, file.filename)

        hasher = hashlib.sha256()
        total = 0
        with open(dest_path, "wb") as out:
            while chunk := file.file.read(1024 * 1024):
                total += len(chunk)
                hasher.update(chunk)
                out.write(chunk)
        
        sample_file = SampleFile(
            sample_id=sample.id,
            file_name=file.filename,
            file_path=dest_path,
            file_type="assembly_fasta",
            file_size=total,
            checksum=hasher.hexdigest(),
        )
        db.add(sample_file)
        sample_ids.append(str(sample.id))
        
        isolate_statuses.append(BatchIsolateStatus(
            sample_id=sample.id,
            filename=file.filename,
            status="QUEUED"
        ))

    batch.total_isolates = len(sample_ids)
    if batch.total_isolates == 0:
        db.rollback()
        raise HTTPException(status_code=400, detail="No valid FASTA files provided.")
        
    db.commit()

    from fastapi import BackgroundTasks
    
    def simulate_workflow():
        from backend.database.session import SessionLocal
        local_db = SessionLocal()
        b = None
        try:
            import time
            from backend.cohort_engine.analyzer import run_full_cohort_analysis
            b = local_db.scalars(select(Batch).where(Batch.id == batch.id)).first()
            if b:
                b.status = "RUNNING"
                local_db.commit()
            
            successful = []
            for s_id in sample_ids:
                time.sleep(2)  # Simulate pipeline
                samp = local_db.scalars(select(Sample).where(Sample.id == s_id)).first()
                if samp:
                    samp.status = "COMPLETED"
                    local_db.commit()
                    if b:
                        b.completed_isolates = (b.completed_isolates or 0) + 1
                        local_db.commit()
                successful.append(s_id)
            
            if run_cohort_analysis:
                if b:
                    b.status = "ISOLATES_COMPLETE"
                    b.cohort_analysis_status = "RUNNING"
                    local_db.commit()
                if len(successful) >= 3:
                    run_full_cohort_analysis(str(batch.id), successful, local_db)
                    if b:
                        b.cohort_analysis_status = "COMPLETED"
                        b.status = "COMPLETED"
                        local_db.commit()
                else:
                    if b:
                        b.cohort_analysis_status = "SKIPPED_INSUFFICIENT_ISOLATES"
                        b.status = "COMPLETED"
                        local_db.commit()
            else:
                if b:
                    b.status = "COMPLETED"
                    local_db.commit()
        except Exception as e:
            if b:
                b.status = "FAILED"
                local_db.commit()
        finally:
            local_db.close()

    background_tasks.add_task(simulate_workflow)

    return BatchResponse(
        batch_id=batch.id,
        project_id=batch.project_id,
        batch_name=batch.batch_name,
        total_isolates=batch.total_isolates,
        status=batch.status,
        completed=batch.completed_isolates,
        failed=batch.failed_isolates,
        running=0,
        cohort_analysis_status=batch.cohort_analysis_status,
        isolates=isolate_statuses
    )

@router.get("/{batch_id}", response_model=BatchResponse)
def get_batch(batch_id: UUID, db: Session = Depends(get_session)):
    """Get status of a batch."""
    batch = db.scalars(
        select(Batch).options(selectinload(Batch.samples)).where(Batch.id == batch_id)
    ).first()
    
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    isolates = []
    running_count = 0
    for s in batch.samples:
        if s.status == "RUNNING":
            running_count += 1
        isolates.append(BatchIsolateStatus(
            sample_id=s.id,
            filename=s.isolate_name,
            status=s.status
        ))

    return BatchResponse(
        batch_id=batch.id,
        project_id=batch.project_id,
        batch_name=batch.batch_name,
        total_isolates=batch.total_isolates,
        status=batch.status,
        completed=batch.completed_isolates,
        failed=batch.failed_isolates,
        running=running_count,
        cohort_analysis_status=batch.cohort_analysis_status,
        isolates=isolates
    )

@router.get("/{batch_id}/cohort", response_model=CohortAnalysisResponse)
def get_batch_cohort(batch_id: UUID, db: Session = Depends(get_session)):
    """Get cohort analysis results for a batch."""
    batch = db.scalars(select(Batch).where(Batch.id == batch_id)).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
        
    results = db.scalars(select(CohortResult).where(CohortResult.batch_id == batch_id)).all()
    
    analyses = {}
    for r in results:
        analyses[r.analysis_type] = r.result_json

    return CohortAnalysisResponse(
        batch_id=batch.id,
        cohort_analysis_status=batch.cohort_analysis_status,
        isolates_analyzed=batch.completed_isolates,
        isolates_failed=batch.failed_isolates,
        analyses=analyses
    )

from fastapi.responses import FileResponse

@router.get("/{batch_id}/plots/{plot_type}", response_class=FileResponse)
def get_batch_plot(batch_id: UUID, plot_type: str):
    """Serve generated R publication plots."""
    allowed_plots = {"umap", "network", "barcode"}
    if plot_type not in allowed_plots:
        raise HTTPException(status_code=400, detail="Invalid plot type")
        
    out_dir = os.path.join(UPLOAD_DIR, f"batch_{batch_id}_plots")
    plot_path = os.path.join(out_dir, f"{plot_type}.png")
    
    if not os.path.exists(plot_path):
        raise HTTPException(status_code=404, detail="Plot not found or not generated yet")
        
    return FileResponse(plot_path, media_type="image/png")

@router.websocket("/{batch_id}/progress")
async def batch_progress(websocket: WebSocket, batch_id: str):
    """WebSocket for real-time batch progress."""
    await websocket.accept()
    # In a real system, this would listen to Redis pub/sub or Celery events.
    # For MVP, we'll poll the DB every few seconds and send updates.
    try:
        while True:
            # Send ping
            await websocket.send_json({"event": "ping", "batch_id": batch_id})
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass
