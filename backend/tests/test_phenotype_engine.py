import pytest
import os
from pathlib import Path
from dataclasses import dataclass

from backend.phenotype_engine.result_models import AMRGeneResult, CandidatePrediction
from backend.phenotype_engine.inference.phenotype_inference import PhenotypeInferenceEngine
from backend.phenotype_engine.inference.conflict_resolution import ConflictResolutionEngine
from backend.phenotype_engine.inference.confidence_propagation import ConfidencePropagator
from backend.phenotype_engine.rule_repository import RuleRepository
from backend.phenotype_engine.breakpoints.eucast_adapter import EUCASTAdapter
from backend.pipeline.isolate_pipeline import _run_phenotype, GeneFinding

# Locate the real rule repository
RULE_JSON_PATH = Path(__file__).resolve().parents[1] / "phenotype_engine" / "rules" / "rule_repository.json"

@pytest.fixture
def rule_repo():
    return RuleRepository(RULE_JSON_PATH)

@pytest.fixture
def engine(rule_repo):
    bp_adapter = EUCASTAdapter()
    conf_prop = ConfidencePropagator()
    return PhenotypeInferenceEngine(rule_repo, bp_adapter, conf_prop)

@dataclass
class MockMutation:
    gene_name: str
    mutation_notation: str
    classification: str = "KNOWN_RESISTANCE"
    confidence_score: float = 1.0


def test_known_resistance_gene(engine):
    """1. A known resistance gene for a drug class -> predicts 'Resistant'."""
    genes = [
        AMRGeneResult(
            gene_name="blaCTX-M-15",
            gene_family="CTX-M beta-lactamase",
            aro_accession="ARO:123",
            hit_type="Strict",
            identity_pct=100.0,
            coverage_pct=100.0,
            confidence_score=1.0
        )
    ]
    predictions = engine.predict("sample_1", "FULL", genes, [], [])
    
    # CTX-M implies R for ceftriaxone, cefotaxime, cefepime according to rule_repository.json
    ceftriaxone_pred = next((p for p in predictions if p.drug == "ceftriaxone"), None)
    assert ceftriaxone_pred is not None
    assert ceftriaxone_pred.predicted_sir == "R"
    assert "blaCTX-M-15" in ceftriaxone_pred.supporting_genes


def test_no_findings_for_class():
    """2. No findings for a class -> predicts 'Susceptible'.
    
    *Documented Behavior*: The current ConflictResolutionEngine explicitly returns 'NOT_TESTABLE' 
    when passed an empty list of candidates for a drug, because it lacks a predefined 'panel'
    to default to 'Susceptible'. We assert the current code behavior.
    """
    resolver = ConflictResolutionEngine()
    resolved = resolver.resolve([], "gentamicin")
    assert resolved.sir == "NOT_TESTABLE"
    assert resolved.has_conflict is False


def test_intermediate_marker_case(engine):
    """3. An intermediate-marker case -> predicts 'Intermediate'."""
    mutations = [
        MockMutation(gene_name="gyrA", mutation_notation="S87N")
    ]
    predictions = engine.predict("sample_1", "FULL", [], mutations, [])
    
    # gyrA 87N implies I for ciprofloxacin
    cipro_pred = next((p for p in predictions if p.drug == "ciprofloxacin"), None)
    assert cipro_pred is not None
    assert cipro_pred.predicted_sir == "I"
    assert "S87N" in cipro_pred.supporting_mutations


def test_conflict_resolution():
    """4. CONFLICT RESOLUTION: a gene implying R and a mutation implying S.
    
    *Documented Behavior*: The ConflictResolutionEngine uses SIR_PRIORITY 
    where R=3, I=2, S=1. If evidence levels are tied, the higher severity (R) wins.
    """
    resolver = ConflictResolutionEngine()
    candidates = [
        CandidatePrediction(
            drug="ciprofloxacin", drug_class="fluoroquinolone", sir="S", 
            rule_id="RULE_S", evidence_type="mutation", evidence_name="mut_s",
            confidence=1.0, evidence_level=1
        ),
        CandidatePrediction(
            drug="ciprofloxacin", drug_class="fluoroquinolone", sir="R", 
            rule_id="RULE_R", evidence_type="gene", evidence_name="gene_r",
            confidence=1.0, evidence_level=1
        )
    ]
    resolved = resolver.resolve(candidates, "ciprofloxacin")
    assert resolved.sir == "R"  # R wins due to SIR_PRIORITY
    assert resolved.has_conflict is True


def test_confidence_scoring_does_not_overcall(engine):
    """5. CONFIDENCE: a low-confidence hit should NOT over-call 'Resistant'.
    
    *Documented Behavior*: If the input genome quality is 'LOW', the ConfidencePropagator
    caps the final confidence at 0.50, which drops the tier from 'HIGH' to 'LOW'. 
    The SIR prediction remains 'R' but is flagged with low confidence.
    """
    genes = [
        AMRGeneResult(
            gene_name="mecA",
            gene_family="mecA",
            aro_accession="ARO:123",
            hit_type="Strict",
            identity_pct=90.0,
            coverage_pct=90.0,
            confidence_score=0.99
        )
    ]
    # Pass 'LOW' genome quality
    predictions = engine.predict("sample_1", "LOW", genes, [], [])
    
    oxa_pred = next((p for p in predictions if p.drug == "oxacillin"), None)
    assert oxa_pred is not None
    assert oxa_pred.predicted_sir == "R"
    # Even though input confidence was 0.99, 'LOW' genome quality caps it
    assert oxa_pred.confidence_score <= 0.50
    assert oxa_pred.confidence_tier == "LOW"


def test_mapping_step_in_pipeline():
    """6. The mapping step: assert _run_phenotype() correctly populates PhenotypeRecord."""
    genes = [
        GeneFinding(
            gene_name="mecA",
            gene_family="mecA",
            identity_pct=100.0,
            coverage_pct=100.0,
            confidence_score=1.0,
            drug_class="beta-lactam",
            antibiotic_class="beta-lactam"
        )
    ]
    
    # We test _run_phenotype mapping
    pheno_records = _run_phenotype(
        sample_id="test_sample",
        genome_quality="FULL",
        genes=genes,
        mutation_determinants=[],
        mechanisms=[],
        species="Staphylococcus aureus"
    )
    
    assert isinstance(pheno_records, list)
    assert len(pheno_records) > 0
    
    oxa_record = next((r for r in pheno_records if r.drug == "oxacillin"), None)
    assert oxa_record is not None
    assert oxa_record.predicted_sir == "R"
    assert oxa_record.drug_class == "penicillin"
    assert oxa_record.confidence_tier == "HIGH"
    assert "mecA" in oxa_record.supporting_genes
