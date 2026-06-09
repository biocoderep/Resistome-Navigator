"""Main Genome Validation Engine orchestrator."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from uuid import UUID

from .ambiguity import analyze_ambiguity
from .complexity import analyze_complexity
from .contig_analysis import analyze_contigs
from .contamination import screen_contamination
from .decision_engine import make_validation_decision
from .duplicate_detector import detect_duplicates
from .gc_analysis import analyze_gc
from .genome_size import validate_genome_size
from .input_validator import InputValidator
from .integrity import compute_integrity
from .kmer_analysis import analyze_kmers
from .models import (
    ValidationConfig,
    ValidationError,
    ValidationReport,
    ValidationStatus,
)
from .quality_scorer import compute_quality_score
from .statistics import compute_assembly_metrics
from .taxonomy import check_taxonomy

logger = logging.getLogger(__name__)


class GenomeValidationEngine:
    """Main orchestrator for genome validation."""

    def __init__(self, config: ValidationConfig | None = None):
        """Initialize validation engine.
        
        Args:
            config: ValidationConfig with thresholds and options.
        """
        self.config = config or ValidationConfig()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def validate(
        self,
        file_path: Path,
        sample_id: UUID | str,
        assembly_id: UUID | str | None = None,
        species: str | None = None,
        progress_callback: Callable[[int, str], None] | None = None,
    ) -> ValidationReport:
        """Run complete genome validation pipeline.
        
        Args:
            file_path: Path to FASTA file to validate.
            sample_id: UUID of sample.
            assembly_id: UUID of assembly (created if None).
            species: Species name if known.
            progress_callback: Function to call with (progress_pct, step_name).
        
        Returns:
            Complete ValidationReport with all sub-reports and decision.
        """
        if assembly_id is None:
            from uuid import uuid4
            assembly_id = str(uuid4())
        
        sample_id = str(sample_id)
        assembly_id = str(assembly_id)
        
        def progress(pct: int, step: str) -> None:
            """Call progress callback if provided."""
            if progress_callback:
                progress_callback(pct, step)
            self.logger.info(f"[{pct}%] {step}")
        
        errors: list[ValidationError] = []
        warnings: list[ValidationError] = []
        
        try:
            # Step 1: Integrity check
            progress(5, "INTEGRITY_CHECK")
            integrity_report = compute_integrity(file_path)
            
            # Step 2: Input validation
            progress(10, "INPUT_VALIDATION")
            input_validator = InputValidator(
                min_contig_length_bp=self.config.min_length_bp
            )
            is_valid, input_errors, input_warnings = input_validator.validate(file_path)
            errors.extend(input_errors)
            warnings.extend(input_warnings)
            
            if not is_valid:
                progress(100, "VALIDATION_FAILED")
                return self._create_failed_report(
                    sample_id, assembly_id, errors, warnings
                )
            
            # Step 3: Compute assembly statistics
            progress(20, "STATISTICS")
            metrics, contigs = compute_assembly_metrics(
                file_path, sample_id, assembly_id
            )
            
            # Step 4: GC analysis
            progress(30, "GC_ANALYSIS")
            gc_report = analyze_gc(contigs)
            gc_outlier_count = len(gc_report.outlier_contigs)
            if gc_report.flag != "OK":
                warnings.append(
                    ValidationError(
                        code="GC_OUTLIERS",
                        detail=gc_report.flag_reason,
                    )
                )
            
            # Step 5: Ambiguity analysis
            progress(40, "AMBIGUITY_ANALYSIS")
            ambiguity_report, ambig_warnings = analyze_ambiguity(
                contigs,
                n_warn_threshold=self.config.n_warn_threshold,
                n_fail_threshold=self.config.n_fail_threshold,
            )
            warnings.extend(ambig_warnings)
            
            # Step 6: Contig analysis
            progress(45, "CONTIG_ANALYSIS")
            contig_report = analyze_contigs(contigs, metrics.total_length_bp / 1_000_000)
            
            # Step 7: Duplicate detection (Phase 2)
            progress(50, "DUPLICATE_DETECTION")
            duplicate_report = detect_duplicates(contigs)
            
            # Step 8: Complexity analysis (Phase 2)
            progress(58, "COMPLEXITY_ANALYSIS")
            complexity_report = analyze_complexity(contigs)
            
            # Step 9: K-mer analysis (Phase 2)
            progress(65, "KMER_ANALYSIS")
            kmer_report = analyze_kmers(
                contigs, run_kmer_analysis=self.config.run_kmer_analysis
            )
            
            # Step 10: Genome size validation
            progress(75, "GENOME_SIZE_VALIDATION")
            size_report, size_warnings = validate_genome_size(
                metrics.total_length_bp, species
            )
            warnings.extend(size_warnings)
            
            # Step 11: Taxonomy check (Phase 2)
            progress(80, "TAXONOMY_CHECK")
            taxonomy_report = check_taxonomy(
                species, metrics.gc_percent, metrics.total_length_bp / 1_000_000
            )
            
            # Step 12: Contamination screening (Phase 2)
            progress(85, "CONTAMINATION_SCREENING")
            contamination_report = screen_contamination(
                gc_outlier_count=gc_outlier_count,
                taxonomy_mismatch=taxonomy_report.taxonomy_status != "CONSISTENT",
                assembly_size_mb=metrics.total_length_bp / 1_000_000,
            )
            
            # Step 13: Quality scoring
            progress(90, "QUALITY_SCORING")
            quality_report = compute_quality_score(
                metrics,
                ambiguity_report,
                size_report,
                contamination_report,
                gc_outlier_count,
            )
            
            # Step 14: Final decision
            progress(95, "VALIDATION_DECISION")
            validation_status = make_validation_decision(
                sample_id=sample_id,
                assembly_id=assembly_id,
                quality_score=quality_report.overall_score,
                quality_class=quality_report.classification,
                n_status=ambiguity_report.n_status,
                n_percent=ambiguity_report.n_percent,
                n_fail_threshold=self.config.n_fail_threshold,
                n_warn_threshold=self.config.n_warn_threshold,
                contamination_risk=contamination_report.risk_level,
                size_status=size_report.size_status,
            )
            
            # Merge all errors/warnings
            errors.extend(validation_status.fail_reasons)
            warnings.extend(validation_status.warnings)
            
            # Build final report
            progress(100, "REPORT_GENERATION")
            report = ValidationReport(
                job_id=sample_id,  # Using sample_id as proxy for job_id
                sample_id=sample_id,
                assembly_id=assembly_id,
                validation_status=validation_status.status,
                quality_score=quality_report.overall_score,
                quality_class=quality_report.classification,
                proceed_to_amr=validation_status.proceed_to_amr,
                confidence_cap=validation_status.confidence_cap,
                errors=[
                    ValidationError(
                        code="VALIDATION_ERROR",
                        detail=str(e) if isinstance(e, str) else e,
                    )
                    if isinstance(e, str)
                    else e
                    for e in errors
                ],
                warnings=[
                    ValidationError(
                        code="VALIDATION_WARNING",
                        detail=str(w) if isinstance(w, str) else w,
                    )
                    if isinstance(w, str)
                    else w
                    for w in warnings
                ],
                assembly_metrics=metrics,
                gc_analysis=gc_report,
                ambiguity_report=ambiguity_report,
                contig_report=contig_report,
                duplicate_contig_report=duplicate_report,
                complexity_report=complexity_report,
                kmer_report=kmer_report,
                genome_size_report=size_report,
                taxonomy_report=taxonomy_report,
                contamination_report=contamination_report,
                quality_score_detail=quality_report,
            )
            
            self.logger.info(
                f"Validation complete: {validation_status.status} "
                f"(quality: {quality_report.classification})"
            )
            return report
            
        except Exception as e:
            self.logger.exception(f"Unexpected error during validation: {e}")
            return self._create_error_report(
                sample_id, assembly_id, str(e)
            )

    def _create_failed_report(
        self,
        sample_id: str,
        assembly_id: str,
        errors: list[ValidationError],
        warnings: list[ValidationError],
    ) -> ValidationReport:
        """Create a failed validation report."""
        return ValidationReport(
            job_id=sample_id,
            sample_id=sample_id,
            assembly_id=assembly_id,
            validation_status="FAIL",
            quality_score=0.0,
            quality_class="FAILED",
            proceed_to_amr=False,
            confidence_cap="FULL",
            errors=errors,
            warnings=warnings,
        )

    def _create_error_report(
        self,
        sample_id: str,
        assembly_id: str,
        error_message: str,
    ) -> ValidationReport:
        """Create an error validation report."""
        return ValidationReport(
            job_id=sample_id,
            sample_id=sample_id,
            assembly_id=assembly_id,
            validation_status="FAIL",
            quality_score=0.0,
            quality_class="FAILED",
            proceed_to_amr=False,
            confidence_cap="FULL",
            errors=[
                ValidationError(
                    code="UNEXPECTED_ERROR",
                    detail=error_message,
                )
            ],
        )


__all__ = ["GenomeValidationEngine"]
