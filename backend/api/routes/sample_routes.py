"""Sample management routes (MVP, no auth)."""

from __future__ import annotations

import hashlib
import os
from datetime import date
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from backend.database.session import get_session
from backend.models.sample import Sample
from backend.models.sample_file import SampleFile
from backend.schemas.sample import (
    SampleDetailResponse,
    SampleFileResponse,
    SampleListResponse,
    SampleResponse,
)

router = APIRouter(prefix="/samples", tags=["samples"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/amr_uploads")
ALLOWED_EXTENSIONS = (".fasta", ".fa", ".fna", ".fasta.gz", ".fa.gz")
MAX_FILE_BYTES = int(os.getenv("MAX_FILE_BYTES", str(2 * 1024 * 1024 * 1024)))


def _validate_extension(filename: str) -> None:
    lower = filename.lower()
    if not lower.endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Unsupported file extension; allowed: "
                + ", ".join(ALLOWED_EXTENSIONS)
            ),
        )


@router.post(
    "/upload",
    response_model=SampleDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a sample and attach an uploaded FASTA file",
)
def upload_sample(
    file: UploadFile = File(...),
    isolate_name: str = Form(..., min_length=1, max_length=200),
    species: str | None = Form(default=None),
    species_taxid: int | None = Form(default=None),
    host: str | None = Form(default=None),
    collection_date: date | None = Form(default=None),
    source_type: str | None = Form(default=None),
    location: str | None = Form(default=None),
    country_code: str | None = Form(default=None),
    file_type: str = Form(default="assembly_fasta"),
    db: Session = Depends(get_session),
) -> SampleDetailResponse:
    """Create a sample, stream the upload to disk, and record the file."""
    if file.filename is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A file with a filename is required.",
        )
    _validate_extension(file.filename)

    from backend.models.batch import Batch
    batch = Batch(
        project_id=None,
        batch_name=f"Single: {isolate_name.strip()}",
        run_cohort_analysis=False,
        total_isolates=1,
        status="DISPATCHING"
    )
    db.add(batch)
    db.flush()

    sample = Sample(
        batch_id=batch.id,
        isolate_name=isolate_name.strip(),
        species=species,
        species_taxid=species_taxid,
        host=host,
        collection_date=collection_date,
        source_type=source_type,
        location=location,
        country_code=country_code,
        status="UPLOADED",
    )
    db.add(sample)
    db.flush()  # assigns sample.id

    sample_dir = os.path.join(UPLOAD_DIR, str(sample.id))
    os.makedirs(sample_dir, exist_ok=True)
    dest_path = os.path.join(sample_dir, file.filename)

    hasher = hashlib.sha256()
    total = 0
    try:
        with open(dest_path, "wb") as out:
            while chunk := file.file.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_FILE_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum size of {MAX_FILE_BYTES} bytes.",
                    )
                hasher.update(chunk)
                out.write(chunk)
    except HTTPException:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise
    finally:
        file.file.close()

    sample_file = SampleFile(
        sample_id=sample.id,
        file_name=file.filename,
        file_path=dest_path,
        file_type=file_type,
        file_size=total,
        checksum=hasher.hexdigest(),
    )
    db.add(sample_file)
    db.commit()
    db.refresh(sample)
    
    # Dispatch single isolate to pipeline
    from backend.tasks.batch_tasks import dispatch_batch_workflow
    dispatch_batch_workflow.apply_async(
        kwargs={
            "batch_id": str(batch.id),
            "sample_ids": [str(sample.id)],
            "run_cohort": False
        }
    )
    
    return SampleDetailResponse.model_validate(sample)


@router.get(
    "",
    response_model=SampleListResponse,
    summary="List samples (paginated, filterable)",
)
def list_samples(
    db: Session = Depends(get_session),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    species: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
) -> SampleListResponse:
    """Return a paginated list of samples with optional filters."""
    filters = []
    if species is not None:
        filters.append(Sample.species == species)
    if status_filter is not None:
        filters.append(Sample.status == status_filter)

    total = db.scalar(
        select(func.count()).select_from(Sample).where(*filters)
    )
    rows = db.scalars(
        select(Sample)
        .where(*filters)
        .order_by(Sample.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return SampleListResponse(
        items=[SampleResponse.model_validate(r) for r in rows],
        total=total or 0,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{sample_id}",
    response_model=SampleDetailResponse,
    summary="Get a sample with its files",
)
def get_sample(
    sample_id: UUID,
    db: Session = Depends(get_session),
) -> SampleDetailResponse:
    """Return a single sample and its associated files."""
    sample = db.scalars(
        select(Sample)
        .options(selectinload(Sample.files))
        .where(Sample.id == sample_id)
    ).first()
    if sample is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sample {sample_id} not found.",
        )
    return SampleDetailResponse.model_validate(sample)


__all__ = ["router"]