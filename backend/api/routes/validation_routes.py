"""Genome validation API routes."""

from __future__ import annotations

import logging
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.session import get_session
from backend.genome_validator import GenomeValidationEngine, ValidationConfig, ValidationReport
from backend.models.genome_validation import Assembly, ValidationReport as ValidationReportModel
from backend.models.sample import Sample
from backend.models.sample_file import SampleFile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/module1/validate", tags=["genome-validation"])


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit genome validation job",
)
def submit_validation(
    sample_id: UUID,
    file_id: UUID,
    assembly_id: UUID | None = None,
    config: dict | None = None,
    db: Session = Depends(get_session),
) -> dict:
    """Submit a genome for validation.
    
    Args:
        sample_id: UUID of sample.
        file_id: UUID of uploaded sample file.
        assembly_id: UUID of assembly (created if not provided).
        config: Optional validation config overrides.
        db: Database session.
    
    Returns:
        Job info with job_id for polling.
    """
    # Validate sample exists
    sample = db.get(Sample, sample_id)
    if not sample:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sample {sample_id} not found",
        )
    
    # Validate file exists
    sample_file = db.get(SampleFile, file_id)
    if not sample_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sample file {file_id} not found",
        )
    
    if sample_file.sample_id != sample_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File does not belong to specified sample",
        )
    
    # Create or get assembly
    if assembly_id is None:
        from uuid import uuid4
        assembly_id = uuid4()
    
    assembly = db.get(Assembly, assembly_id)
    if not assembly:
        assembly = Assembly(
            id=assembly_id,
            sample_id=sample_id,
            file_path=sample_file.file_path,
            status="VALIDATING",
        )
        db.add(assembly)
        db.commit()
    
    try:
        # Run validation synchronously (MVP)
        # In production, this would be dispatched to Celery
        validation_config = ValidationConfig(**(config or {}))
        engine = GenomeValidationEngine(config=validation_config)
        
        file_path = Path(sample_file.file_path)
        report: ValidationReport = engine.validate(
            file_path=file_path,
            sample_id=sample_id,
            assembly_id=assembly_id,
            species=sample.species,
        )
        
        # Store validation report in DB
        from backend.models.genome_validation import AssemblyMetrics
        
        # Update assembly metrics
        if report.assembly_metrics:
            metrics = db.query(AssemblyMetrics).filter_by(assembly_id=assembly_id).first()
            if not metrics:
                metrics = AssemblyMetrics(
                    assembly_id=assembly_id,
                    total_length_bp=report.assembly_metrics.total_length_bp,
                    contig_count=report.assembly_metrics.contig_count,
                    mean_contig_bp=report.assembly_metrics.mean_contig_bp,
                    median_contig_bp=report.assembly_metrics.median_contig_bp,
                    max_contig_bp=report.assembly_metrics.max_contig_bp,
                    min_contig_bp=report.assembly_metrics.min_contig_bp,
                    n50_bp=report.assembly_metrics.n50_bp,
                    n90_bp=report.assembly_metrics.n90_bp,
                    l50=report.assembly_metrics.l50,
                    gc_percent=report.assembly_metrics.gc_percent,
                    n_percent=report.assembly_metrics.n_percent,
                    assembly_span_bp=report.assembly_metrics.assembly_span_bp,
                    quality_score=report.quality_score,
                    quality_classification=report.quality_class,
                    confidence_cap=report.confidence_cap,
                    contamination_risk=report.contamination_report.risk_level if report.contamination_report else None,
                )
                db.add(metrics)
        
        # Store validation report
        validation_record = ValidationReportModel(
            assembly_id=assembly_id,
            validation_status=report.validation_status,
            quality_score=report.quality_score,
            quality_class=report.quality_class,
            proceed_to_amr=report.proceed_to_amr,
            confidence_cap=report.confidence_cap,
            full_report=report.model_dump(),
            errors=[e.model_dump() for e in report.errors] if report.errors else None,
            warnings=[w.model_dump() for w in report.warnings] if report.warnings else None,
        )
        db.add(validation_record)
        
        # Update assembly status
        assembly.status = "VALIDATED" if report.proceed_to_amr else "VALIDATION_FAILED"
        db.commit()
        
        logger.info(
            f"Validation completed for sample {sample_id}: {report.validation_status}"
        )
        
        return {
            "status": "success",
            "data": {
                "sample_id": str(sample_id),
                "assembly_id": str(assembly_id),
                "validation_status": report.validation_status,
                "quality_score": report.quality_score,
                "quality_class": report.quality_class,
                "proceed_to_amr": report.proceed_to_amr,
                "confidence_cap": report.confidence_cap,
            },
        }
        
    except Exception as e:
        logger.exception(f"Error during validation: {e}")
        assembly.status = "VALIDATION_ERROR"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}",
        )


@router.get(
    "/{assembly_id}",
    summary="Get validation results for assembly",
)
def get_validation_results(
    assembly_id: UUID,
    db: Session = Depends(get_session),
) -> dict:
    """Get validation results for an assembly.
    
    Args:
        assembly_id: UUID of assembly.
        db: Database session.
    
    Returns:
        Complete validation report.
    """
    assembly = db.get(Assembly, assembly_id)
    if not assembly:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assembly {assembly_id} not found",
        )
    
    # Get latest validation report
    from sqlalchemy import desc, select
    
    report_query = (
        select(ValidationReportModel)
        .filter_by(assembly_id=assembly_id)
        .order_by(desc(ValidationReportModel.created_at))
        .limit(1)
    )
    latest_report = db.scalars(report_query).first()
    
    if not latest_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No validation report found for assembly {assembly_id}",
        )
    
    return {
        "status": "success",
        "data": latest_report.full_report,
    }


__all__ = ["router"]
