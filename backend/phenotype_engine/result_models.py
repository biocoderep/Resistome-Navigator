"""Data models for phenotype prediction engine - Module 1E v1.0.0"""

from dataclasses import dataclass, field
from typing import List, Literal, Optional

# Simplified representation of the input from previous engines
@dataclass
class AMRGeneResult:
    gene_name: str
    gene_family: str
    aro_accession: Optional[str]
    hit_type: str
    identity_pct: float
    coverage_pct: float
    confidence_score: float
    mechanism_type: Optional[str] = None

@dataclass
class CandidatePrediction:
    """Raw, unresolved prediction from a single rule."""
    drug: str
    drug_class: str
    sir: str  # "S", "I", "R", "NOT_TESTABLE", "INDETERMINATE"
    rule_id: str
    evidence_type: str  # "gene", "mutation", "mechanism", "combo"
    evidence_name: str
    confidence: float
    evidence_level: int
    organism: Optional[str] = None

@dataclass
class ResolvedPrediction:
    """Conflict-resolved prediction for a specific drug."""
    drug: str
    sir: str
    confidence: float
    winning_rule: str
    winning_rule_evidence_level: int
    winning_rule_weight: float
    all_evidence: List[CandidatePrediction]
    has_conflict: bool
    drug_class: str = ""

@dataclass
class PhenotypePrediction:
    """Final, fully annotated prediction ready for export."""
    prediction_id: str
    sample_id: str
    drug: str
    drug_class: str
    antibiotic_class: str
    predicted_sir: str
    confidence_score: float
    confidence_tier: str  # "HIGH", "MEDIUM", "LOW"
    breakpoint_source: str
    breakpoint_version: str
    is_not_testable: bool
    has_conflict: bool
    
    supporting_genes: List[str] = field(default_factory=list)
    supporting_mutations: List[str] = field(default_factory=list)
    supporting_mechanisms: List[str] = field(default_factory=list)
    supporting_rules: List[str] = field(default_factory=list)
    all_candidates: List[CandidatePrediction] = field(default_factory=list)
    
    explanation: str = ""
