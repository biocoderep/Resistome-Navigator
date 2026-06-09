"""Decision engine - PASS/WARNING/FAIL determination."""

from __future__ import annotations

from .models import ValidationStatus


def make_validation_decision(
    sample_id: str,
    assembly_id: str | None,
    quality_score: float,
    quality_class: str,
    n_status: str,
    n_percent: float,
    n_fail_threshold: float,
    n_warn_threshold: float,
    contamination_risk: str,
    size_status: str,
    override_status: str | None = None,
) -> ValidationStatus:
    """Determine final PASS/WARNING/FAIL status.
    
    Decision rules (per spec Section 16.1):
    - Critical FASTA error → FAIL (no override)
    - Genome too small (< 0.5 Mb) → FAIL (no override)
    - Genome too large (> 15 Mb) → FAIL (admin override only)
    - N% too high (> fail_threshold) → FAIL (user override)
    - High contamination → FAIL (user override)
    - Quality score < 40 → FAIL (user override)
    - N% warning (warn_threshold to fail_threshold) → WARNING
    - Moderate contamination → WARNING
    - Poor quality (40-54) → WARNING
    - All checks pass, quality >= 55 → PASS
    """
    fail_reasons: list[str] = []
    warnings: list[str] = []
    status = "PASS"
    confidence_cap = "FULL"
    proceed_to_amr = True
    
    # Critical checks (hard fail, no override)
    # (These would be caught before decision engine)
    
    # Size checks
    if size_status == "FAIL":
        if "too large" in size_status.lower() and override_status != "ADMIN_OVERRIDE":
            fail_reasons.append("Genome size exceeds maximum threshold (may require admin override)")
            status = "FAIL"
            proceed_to_amr = False
        elif "too small" in size_status.lower():
            fail_reasons.append("Genome size below minimum threshold")
            status = "FAIL"
            proceed_to_amr = False
    
    # N% checks
    if n_percent > n_fail_threshold:
        if override_status == "USER_OVERRIDE":
            warnings.append(f"N% ({n_percent:.2f}%) exceeds fail threshold; USER_OVERRIDE applied")
            status = "WARNING" if status != "FAIL" else "FAIL"
            confidence_cap = "LOW"
        else:
            fail_reasons.append(f"N% ({n_percent:.2f}%) exceeds fail threshold ({n_fail_threshold}%)")
            status = "FAIL"
            proceed_to_amr = False
    elif n_percent > n_warn_threshold:
        warnings.append(f"N% ({n_percent:.2f}%) exceeds warning threshold ({n_warn_threshold}%)")
        if status != "FAIL":
            status = "WARNING"
        confidence_cap = "MEDIUM"
    
    # Contamination checks
    if contamination_risk == "HIGH_RISK":
        if override_status == "USER_OVERRIDE":
            warnings.append("HIGH contamination risk; USER_OVERRIDE applied")
            status = "WARNING" if status != "FAIL" else "FAIL"
            confidence_cap = "LOW"
        else:
            fail_reasons.append("HIGH contamination risk detected")
            status = "FAIL"
            proceed_to_amr = False
    elif contamination_risk == "MODERATE_RISK":
        warnings.append("MODERATE contamination risk")
        if status != "FAIL":
            status = "WARNING"
        confidence_cap = "MEDIUM"
    
    # Quality score checks
    if quality_score < 40:
        if override_status == "USER_OVERRIDE":
            warnings.append(f"Quality score ({quality_score:.1f}) below 40; USER_OVERRIDE applied")
            status = "WARNING" if status != "FAIL" else "FAIL"
            confidence_cap = "LOW"
        else:
            fail_reasons.append(f"Quality score ({quality_score:.1f}) below 40 threshold")
            status = "FAIL"
            proceed_to_amr = False
    elif quality_score < 55:
        warnings.append(f"Quality score ({quality_score:.1f}) in POOR range (40-54)")
        if status != "FAIL":
            status = "WARNING"
        confidence_cap = "MEDIUM"
    
    # Override tracking
    override_by = None
    override_at = None
    if override_status:
        override_by = override_status
        from datetime import datetime
        override_at = datetime.utcnow()
    
    return ValidationStatus(
        sample_id=sample_id,
        assembly_id=assembly_id,
        status=status,
        quality_class=quality_class,
        quality_score=quality_score,
        fail_reasons=fail_reasons,
        warnings=warnings,
        override_status=override_status,
        override_by=override_by,
        override_at=override_at,
        proceed_to_amr=proceed_to_amr,
        confidence_cap=confidence_cap,
    )


__all__ = ["make_validation_decision"]
