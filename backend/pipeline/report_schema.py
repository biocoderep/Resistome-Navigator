"""Pydantic schema for the canonical per-isolate AMR report.

This is the machine-readable contract emitted by the Nextflow pipeline
(``amr_detection_report.json``) and consumed by ``backend/tasks/batch_tasks.py``
for DB ingestion. Every record field maps 1:1 onto the corresponding ORM model
column, so ingestion is a straight field copy.

Written to be compatible with both Pydantic v1 and v2; use :func:`dump_model`
to serialise regardless of installed version.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def dump_model(model: BaseModel) -> dict:
    """Serialise a Pydantic model to a plain dict on either v1 or v2."""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


class AmrGeneRecord(BaseModel):
    """Maps to ``backend.models.amr_gene.AmrGene``."""

    gene_name: str
    gene_family: Optional[str] = None
    antibiotic_class: Optional[str] = None
    drug_class: Optional[str] = None
    resistance_mechanism: Optional[str] = None
    identity_percent: Optional[float] = None
    coverage_percent: Optional[float] = None
    contig_id: Optional[str] = None
    start_position: Optional[int] = None
    end_position: Optional[int] = None
    strand: Optional[str] = None
    tool_name: Optional[str] = None
    evidence_level: int = 3
    confidence_score: Optional[float] = None
    confidence_tier: Optional[str] = None


class VirulenceGeneRecord(BaseModel):
    """Maps to ``backend.models.virulence_gene.VirulenceGene``."""

    gene_name: str
    virulence_factor: Optional[str] = None
    virulence_category: Optional[str] = None
    mechanism: Optional[str] = None
    identity_percent: Optional[float] = None
    coverage_percent: Optional[float] = None
    contig_id: Optional[str] = None
    start_position: Optional[int] = None
    end_position: Optional[int] = None
    is_high_risk: bool = False
    risk_weight: float = 0.0
    database_source: Optional[str] = None
    confidence_score: Optional[float] = None


class MutationRecord(BaseModel):
    """Maps to ``backend.models.resistance_mutation.ResistanceMutation``."""

    gene_name: str
    mutation: str
    protein_position: Optional[int] = None
    ref_amino_acid: Optional[str] = None
    alt_amino_acid: Optional[str] = None
    effect: Optional[str] = None
    mechanism: Optional[str] = None
    classification: Optional[str] = None
    drug_class: Optional[str] = None
    drugs_affected: List[str] = Field(default_factory=list)
    sir_prediction: Optional[str] = None
    identity_percent: Optional[float] = None
    coverage_percent: Optional[float] = None
    contig_id: Optional[str] = None
    hgvs_protein: Optional[str] = None
    hgvs_cdna: Optional[str] = None
    domain: Optional[str] = None
    database_source: Optional[str] = "knowledgebase"
    confidence_score: Optional[float] = None
    confidence_tier: Optional[str] = None


class MechanismRecord(BaseModel):
    mechanism_code: str
    mechanism_name: str
    drug_classes: List[str] = Field(default_factory=list)
    supporting_genes: List[str] = Field(default_factory=list)
    supporting_mutations: List[str] = Field(default_factory=list)
    evidence_sources: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    confidence_tier: str = "LOW"


class DrugAssociationRecord(BaseModel):
    drug_name: str
    drug_class: str
    sir_prediction: str
    evidence_type: str
    evidence_name: str
    evidence_level: int
    confidence: float
    cross_resistance: List[str] = Field(default_factory=list)


class PhenotypeRecord(BaseModel):
    """Maps to ``backend.models.phenotype_prediction.PhenotypePrediction``."""

    drug: str
    drug_class: Optional[str] = None
    predicted_sir: str
    confidence_score: Optional[float] = None
    confidence_tier: Optional[str] = None
    breakpoint_source: Optional[str] = None
    breakpoint_version: Optional[str] = None
    is_not_testable: bool = False
    has_conflict: bool = False
    supporting_genes: List[str] = Field(default_factory=list)
    supporting_mutations: List[str] = Field(default_factory=list)
    explanation: Optional[str] = None


class ConfidenceScoreRecord(BaseModel):
    """Maps to ``backend.models.confidence_score.ConfidenceScore``."""

    context: str
    target_name: str
    overall_score: float
    tier: str
    cap_applied: bool = False
    components: Dict[str, Any] = Field(default_factory=dict)
    weighted: Dict[str, Any] = Field(default_factory=dict)


class PathogenicitySummary(BaseModel):
    total_vf_genes: int = 0
    category_diversity: int = 0
    high_risk_count: int = 0
    high_risk_genes: List[str] = Field(default_factory=list)
    categories_detected: List[str] = Field(default_factory=list)
    category_summary: Dict[str, int] = Field(default_factory=dict)
    risk_score: float = 0.0
    risk_class: str = "LOW"


class ReportSummary(BaseModel):
    total_amr_genes: int = 0
    total_virulence_genes: int = 0
    total_mutations: int = 0
    total_novel_mutations: int = 0
    total_mechanisms: int = 0
    total_resistant_phenotypes: int = 0
    resistance_classes: List[str] = Field(default_factory=list)


class IsolateReport(BaseModel):
    """Canonical per-isolate report (single source of truth for ingestion)."""

    report_version: str = "2.0"
    sample_id: str
    species: Optional[str] = None
    generated_at: str
    pipeline_stage: str = "Module 1 - AMR Characterisation"
    genome_quality: str = "LOW"
    validation_status: Optional[str] = None
    virulence_status: str = "not_run"

    amr_genes: List[AmrGeneRecord] = Field(default_factory=list)
    virulence_genes: List[VirulenceGeneRecord] = Field(default_factory=list)
    mutations: List[MutationRecord] = Field(default_factory=list)
    mechanisms: List[MechanismRecord] = Field(default_factory=list)
    drug_associations: List[DrugAssociationRecord] = Field(default_factory=list)
    phenotypes: List[PhenotypeRecord] = Field(default_factory=list)
    confidence_scores: List[ConfidenceScoreRecord] = Field(default_factory=list)
    pathogenicity: PathogenicitySummary = Field(default_factory=PathogenicitySummary)
    summary: ReportSummary = Field(default_factory=ReportSummary)

    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


__all__ = [
    "AmrGeneRecord",
    "VirulenceGeneRecord",
    "MutationRecord",
    "MechanismRecord",
    "DrugAssociationRecord",
    "PhenotypeRecord",
    "ConfidenceScoreRecord",
    "PathogenicitySummary",
    "ReportSummary",
    "IsolateReport",
    "dump_model",
]
