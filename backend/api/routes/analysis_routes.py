"""Analysis job routes (MVP, no auth)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.database.session import get_session
from backend.models.amr_gene import AmrGene
from backend.models.analysis_job import AnalysisJob
from backend.models.sample import Sample
from backend.schemas.analysis import (
    AnalysisJobDetailResponse,
    AnalysisJobResponse,
    AnalysisRunRequest,
)

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post(
    "/run",
    response_model=AnalysisJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit an analysis job for a sample",
)
def run_analysis(
    payload: AnalysisRunRequest,
    db: Session = Depends(get_session),
) -> AnalysisJobResponse:
    """Create a queued analysis job. Execution is handled out of band."""
    sample = db.get(Sample, payload.sample_id)
    if sample is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sample {payload.sample_id} not found.",
        )

    job = AnalysisJob(
        sample_id=payload.sample_id,
        job_type=payload.job_type,
        status="QUEUED",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return AnalysisJobResponse.model_validate(job)


@router.get(
    "/{job_id}",
    response_model=AnalysisJobDetailResponse,
    summary="Get an analysis job with its AMR gene results",
)
def get_analysis_job(
    job_id: UUID,
    db: Session = Depends(get_session),
) -> AnalysisJobDetailResponse:
    """Return a job, its status, and any detected AMR genes (with hits)."""
    job = db.scalars(
        select(AnalysisJob)
        .options(
            selectinload(AnalysisJob.amr_genes).selectinload(AmrGene.hits)
        )
        .where(AnalysisJob.id == job_id)
    ).first()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis job {job_id} not found.",
        )
    return AnalysisJobDetailResponse.model_validate(job)


__all__ = ["router"]