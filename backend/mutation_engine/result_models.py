"""Data models for mutation detection and mechanism classification."""

from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum
from uuid import UUID
from datetime import datetime


class VariantType(str, Enum):
    """Variant types."""
    SNP = "SNP"
    INSERTION = "INS"
    DELETION = "DEL"
    FRAMESHIFT = "FRAMESHIFT"
    STOP_CODON = "STOP"
    PROMOTER = "PROMOTER"


class MutationEffect(str, Enum):
    """Amino acid change effects."""
    MISSENSE = "missense"
    NONSENSE = "nonsense"
    SILENT = "silent"
    FRAMESHIFT = "frameshift"
    INFRAME_INDEL = "inframe_indel"


class MutationClassification(str, Enum):
    """Mutation classification."""
    KNOWN_RESISTANCE = "KNOWN_RESISTANCE"
    LIKELY_RESISTANCE = "LIKELY_RESISTANCE"
    NOVEL_IN_DOMAIN = "NOVEL_IN_DOMAIN"
    NOVEL = "NOVEL"
    UNKNOWN = "UNKNOWN"
    SILENT = "SILENT"


class ConfidenceTier(str, Enum):
    """Confidence levels."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class SIRPrediction(str, Enum):
    """SIR predictions."""
    SUSCEPTIBLE = "S"
    INTERMEDIATE = "I"
    RESISTANT = "R"
    UNKNOWN = "U"
    INDETERMINATE = "INDETERMINATE"


@dataclass
class RawVariant:
    """Single raw variant from alignment."""
    gene_name: str
    cds_position: int  # 1-based
    protein_position: int
    ref_nucleotide: str
    alt_nucleotide: str
    ref_amino_acid: Optional[str]  # 1-letter code
    alt_amino_acid: Optional[str]
    variant_type: VariantType
    codon_ref: Optional[str]
    codon_alt: Optional[str]
    alignment_quality: float  # 0.0-1.0


@dataclass
class AnnotatedVariant:
    """Variant with HGVS notation and annotations."""
    raw_variant: RawVariant
    mutation_notation: str  # e.g., "gyrA S83L"
    hgvs_protein: str  # p.Ser83Leu
    hgvs_cdna: str  # c.248C>T
    effect: MutationEffect
    domain: Optional[str] = None  # e.g., "QRDR"
    contig_id: Optional[str] = None
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None


@dataclass
class MutationMapping:
    """KB mapping result for a variant."""
    classification: MutationClassification
    kb_entry: Optional[dict] = None
    confidence: float = 0.5


@dataclass
class MutationConfidence:
    """Confidence metrics for a mutation."""
    alignment_quality: float
    kb_evidence: float
    gene_coverage: float
    classification_score: float
    final_score: float
    confidence_tier: ConfidenceTier


@dataclass
class ResistanceDeterminant:
    """Unified resistance element (gene or mutation) with mechanism and drug effects."""
    determinant_id: UUID
    determinant_type: str  # "gene" | "mutation" | "gene_mutation"
    
    # Identity
    gene_name: str
    
    # Mechanism
    mechanism_code: str
    mechanism_name: str
    
    # Drug associations
    drug_class: str
    
    mutation_notation: Optional[str] = None
    aro_accession: Optional[str] = None
    mechanism_subclass: Optional[str] = None
    drugs_affected: List[str] = field(default_factory=list)
    sir_prediction: SIRPrediction = SIRPrediction.UNKNOWN
    
    # Evidence
    evidence_level: int = 5  # 1-5 (1=highest)
    supporting_dbs: List[str] = field(default_factory=list)
    classification: MutationClassification = MutationClassification.UNKNOWN
    
    # Scores
    confidence_score: float = 0.0
    confidence_tier: ConfidenceTier = ConfidenceTier.LOW
    priority_score: float = 0.0
    
    # Genomic location
    contig_id: Optional[str] = None
    start: Optional[int] = None
    end: Optional[int] = None
    strand: Optional[str] = None
    
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MechanismObject:
    """Aggregated resistance mechanism with supporting evidence."""
    mechanism_code: str
    mechanism_name: str
    mechanism_subclass: Optional[str]
    drug_classes: List[str]
    
    supporting_genes: List[str] = field(default_factory=list)
    supporting_mutations: List[str] = field(default_factory=list)
    evidence_sources: List[str] = field(default_factory=list)
    
    confidence: float = 0.0
    confidence_tier: ConfidenceTier = ConfidenceTier.LOW


@dataclass
class DrugAssociation:
    """Drug-specific resistance prediction."""
    drug_name: str
    drug_class: str
    sir_prediction: SIRPrediction
    evidence_type: str  # "gene" | "mutation" | "mechanism"
    evidence_name: str
    evidence_level: int
    confidence: float
    cross_resistance: List[str] = field(default_factory=list)


@dataclass
class MutationDetectionResult:
    """Results from mutation detection engine."""
    job_id: str
    sample_id: UUID
    assembly_id: UUID
    
    mutations: List[AnnotatedVariant] = field(default_factory=list)
    novel_mutations: List[AnnotatedVariant] = field(default_factory=list)
    confidence_scores: dict = field(default_factory=dict)
    
    total_mutations: int = 0
    total_novel: int = 0
    
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    completed_at: Optional[datetime] = None
