"""Data models for virulence engine - Module 1F v1.0.0"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

@dataclass
class VirulenceRawHit:
    tool: str
    gene_name: str
    identity_pct: float
    coverage_pct: float
    db_version_id: str
    vf_category: str = "unknown"
    vf_function: str = ""
    contig_id: str = ""
    start: int = 0
    end: int = 0
    bit_score: float = 0.0
    e_value: float = 1.0
    strand: str = "+"

@dataclass
class VirulenceFactor:
    vf_id: str
    sample_id: str
    gene_name: str
    category_code: str
    category_display: str
    function_description: str
    detection_tool: str
    db_version_id: str
    identity_pct: float
    coverage_pct: float
    bit_score: float
    e_value: float
    contig_id: str
    start: int
    end: int
    strand: str
    is_high_risk: bool
    risk_weight: float
    confidence: Any  # Will hold ConfidenceResult from amr_confidence
    vfdb_id: Optional[str] = None

@dataclass
class PathogenicityProfile:
    sample_id: str
    total_vf_genes: int
    categories_detected: List[str]
    category_diversity: int
    high_risk_count: int
    high_risk_genes: List[str]
    unique_determinants: List[str]
    risk_score: float
    risk_class: str
    category_summary: Dict[str, int]
    confidence: float
