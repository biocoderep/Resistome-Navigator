"""Celery task for genome validation (Phase 2 - async implementation)."""

from __future__ import annotations

import logging
from pathlib import Path
from uuid import UUID

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="module1.validate_genome",
    max_retries=3,
    default_retry_delay=30,
    soft_time_limit=1800,  # 30 min
    time_limit=2100,  # 35 min hard kill
    track_started=True,
)
def validate_genome_task(
    self,
    job_id: str,
    sample_id: str,
    assembly_id: str,
    file_path: str,
    species: str | None = None,
    config_dict: dict | None = None,
) -> dict:
    """Celery task for async genome validation.
    
    Args:
        job_id: Job ID for tracking.
        sample_id: Sample UUID.
        assembly_id: Assembly UUID.
        file_path: Path to FASTA file.
        species: Species name if known.
        config_dict: Validation config overrides.
    
    Returns:
        Dictionary with validation results.
    """
    try:
        from backend.genome_validator import GenomeValidationEngine, ValidationConfig
        from sqlalchemy.orm import Session
        from backend.database.session import SessionLocal
        from backend.models.genome_validation import ValidationReport as ValidationReportModel
        from backend.models.genome_validation import AssemblyMetrics
        
        # Progress callback
        def progress(pct: int, step: str) -> None:
            self.update_state(
                state="RUNNING",
                meta={"progress": pct, "current_step": step, "job_id": job_id},
            )
        
        # Run validation
        config = ValidationConfig(**(config_dict or {}))
        engine = GenomeValidationEngine(config=config)
        
        report = engine.validate(
            file_path=Path(file_path),
            sample_id=sample_id,
            assembly_id=assembly_id,
            species=species,
            progress_callback=progress,
        )
        
        # Store results in DB
        db: Session = SessionLocal()
        try:
            # Store metrics if present
            if report.assembly_metrics:
                existing_metrics = (
                    db.query(AssemblyMetrics)
                    .filter_by(assembly_id=assembly_id)
                    .first()
                )
                if not existing_metrics:
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
                    )
                    db.add(metrics)
            
            # Store validation report
            validation_record = ValidationReportModel(
                assembly_id=assembly_id,
                job_id=job_id,
                validation_status=report.validation_status,
                quality_score=report.quality_score,
                quality_class=report.quality_class,
                proceed_to_amr=report.proceed_to_amr,
                confidence_cap=report.confidence_cap,
                full_report=report.model_dump(),
            )
            db.add(validation_record)
            db.commit()
        finally:
            db.close()
        
        logger.info(
            f"Validation task completed: {report.validation_status} "
            f"(quality: {report.quality_class})"
        )
        
        return {
            "status": "COMPLETED",
            "validation_status": report.validation_status,
            "quality_score": report.quality_score,
            "quality_class": report.quality_class,
            "proceed_to_amr": report.proceed_to_amr,
            "confidence_cap": report.confidence_cap,
        }
        
    except Exception as exc:
        logger.exception(f"Validation task failed: {exc}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


__all__ = ["validate_genome_task"]
