import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import uuid

from .adapters.vfdb_adapter import VFDBAdapter
from .virulence_classifier import VirulenceClassifier
from .pathogenicity_profile import compute_pathogenicity_profile
from .result_models import VirulenceFactor, PathogenicityProfile
from backend.amr_confidence.confidence_aggregation import aggregate

logger = logging.getLogger(__name__)

class VirulenceDetectionResult:
    def __init__(self, status: str, virulence_genes: List[VirulenceFactor], pathogenicity_profile: Optional[PathogenicityProfile] = None, errors: List[str] = None):
        self.status = status  # "completed" | "not_run"
        self.virulence_genes = virulence_genes
        self.pathogenicity_profile = pathogenicity_profile
        self.errors = errors or []

class VirulenceDetectionEngine:
    def __init__(self):
        self.ontology_path = Path(__file__).parent / "ontology" / "virulence_ontology.json"
        self.gene_map_path = Path(__file__).parent / "ontology" / "gene_category_map.json"
        self.classifier = None
        self.vfdb = VFDBAdapter()
        
    def _init_classifier(self):
        if not self.classifier:
            if self.ontology_path.exists() and self.gene_map_path.exists():
                self.classifier = VirulenceClassifier(self.ontology_path, self.gene_map_path)
            else:
                logger.warning("Virulence ontology files not found.")
                
    def run(self, sample_id: str, analysis_results_dir: Path, genome_quality: str = "FULL", reference_length: int = 1000) -> VirulenceDetectionResult:
        """Run the virulence pipeline by parsing external tool output."""
        
        # We expect abricate_vfdb.tsv in the analysis_results_dir
        tsv_file = analysis_results_dir / "abricate_vfdb.tsv"
        
        # 1. Check for missing input file (CRITICAL REQUIREMENT)
        if not tsv_file.exists():
            msg = f"Virulence tool output not found at {tsv_file}. Skipping virulence detection."
            logger.warning(msg)
            return VirulenceDetectionResult(
                status="not_run",
                virulence_genes=[],
                pathogenicity_profile=None,
                errors=[msg]
            )
            
        self._init_classifier()
            
        # 2. Parse real TSV
        raw_hits = self.vfdb.parse_results(tsv_file)
        
        if not raw_hits:
            # File exists but is empty / no findings
            return VirulenceDetectionResult(
                status="completed",
                virulence_genes=[],
                pathogenicity_profile=None, # or an empty profile
                errors=[]
            )
            
        # 3. Classify and map
        factors = []
        for hit in raw_hits:
            if self.classifier:
                cls_data = self.classifier.classify(hit)
            else:
                # Fallback if ontology is missing
                cls_data = {
                    "category_code": "unknown", "category_display": "Unknown", 
                    "risk_weight": 0.1, "is_high_risk": False
                }
                
            # Confidence Scoring
            conf_result = aggregate(
                identity_pct=hit.identity_pct,
                coverage_pct=hit.coverage_pct,
                bit_score=hit.bit_score,
                e_value=hit.e_value,
                supporting_tools=[hit.tool],
                evidence_types=["computational"],
                context="virulence",
                genome_quality=genome_quality,
                reference_length=reference_length
            )
            
            factor = VirulenceFactor(
                vf_id=str(uuid.uuid4()),
                sample_id=sample_id,
                gene_name=hit.gene_name,
                category_code=cls_data["category_code"],
                category_display=cls_data["category_display"],
                function_description=hit.vf_function,
                detection_tool=hit.tool,
                db_version_id=hit.db_version_id,
                identity_pct=hit.identity_pct,
                coverage_pct=hit.coverage_pct,
                bit_score=hit.bit_score,
                e_value=hit.e_value,
                contig_id=hit.contig_id,
                start=hit.start,
                end=hit.end,
                strand=hit.strand,
                is_high_risk=cls_data["is_high_risk"],
                risk_weight=cls_data["risk_weight"],
                confidence=conf_result,
                vfdb_id=None
            )
            factors.append(factor)
            
        # 4. Profile
        profile = compute_pathogenicity_profile(sample_id, factors)
        
        return VirulenceDetectionResult(
            status="completed",
            virulence_genes=factors,
            pathogenicity_profile=profile,
            errors=[]
        )
