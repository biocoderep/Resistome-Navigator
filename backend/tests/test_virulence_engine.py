"""Tests for the Virulence Engine following the ABRICATE/TSV spec."""

import tempfile
import pytest
from pathlib import Path
from backend.virulence_engine.engine import VirulenceDetectionEngine

@pytest.fixture
def mock_ontology_dir(tmp_path):
    # Setup temporary ontology files to ensure classifier initiates
    ontology_dir = tmp_path / "ontology"
    ontology_dir.mkdir(parents=True)
    
    (ontology_dir / "virulence_ontology.json").write_text('{"categories": [{"code": "toxin", "display": "Toxin", "risk_weight": 0.9}], "high_risk_categories": ["toxin"], "high_risk_genes": ["stx1"]}')
    (ontology_dir / "gene_category_map.json").write_text('{"stx1": "toxin", "fimh": "adhesin"}')
    return ontology_dir

@pytest.fixture
def engine(mock_ontology_dir, monkeypatch):
    e = VirulenceDetectionEngine()
    e.ontology_path = mock_ontology_dir / "virulence_ontology.json"
    e.gene_map_path = mock_ontology_dir / "gene_category_map.json"
    return e

def test_missing_tsv_fallback(engine, tmp_path):
    """Case C: Missing file -> status 'not_run', empty genes, warning logged."""
    # Analysis results dir has no TSV
    result = engine.run("SAMPLE1", tmp_path)
    
    assert result.status == "not_run"
    assert len(result.virulence_genes) == 0
    assert result.pathogenicity_profile is None
    assert len(result.errors) == 1
    assert "not found" in result.errors[0]

def test_empty_tsv_fallback(engine, tmp_path):
    """Case B: Present-but-empty TSV -> status 'completed', empty list."""
    tsv = tmp_path / "abricate_vfdb.tsv"
    tsv.write_text("FILE\tSEQUENCE\tSTART\tEND\tSTRAND\tGENE\tCOVERAGE\tCOVERAGE_MAP\tGAPS\t%COVERAGE\t%IDENTITY\tDATABASE\tACCESSION\tPRODUCT\tRESISTANCE\n")
    
    result = engine.run("SAMPLE2", tmp_path)
    
    assert result.status == "completed"
    assert len(result.virulence_genes) == 0
    assert result.pathogenicity_profile is None

def test_populated_tsv_parsing(engine, tmp_path):
    """Case A & D: Populated TSV -> genes parsed correctly and risk score computed."""
    tsv = tmp_path / "abricate_vfdb.tsv"
    # Write a valid ABRICATE row for stx1 (which is high risk)
    tsv.write_text(
        "FILE\tSEQUENCE\tSTART\tEND\tSTRAND\tGENE\tCOVERAGE\tCOVERAGE_MAP\tGAPS\t%COVERAGE\t%IDENTITY\tDATABASE\tACCESSION\tPRODUCT\n"
        "input.fa\tcontig_1\t100\t1000\t+\tstx1\t1-900\t===\t0\t100.0\t99.5\tvfdb\tVF0001\tShiga toxin 1\n"
        "input.fa\tcontig_2\t500\t1500\t+\tfimH\t1-1000\t===\t0\t95.0\t90.0\tvfdb\tVF0002\tType 1 fimbrial adhesin\n"
    )
    
    result = engine.run("SAMPLE3", tmp_path)
    
    assert result.status == "completed"
    assert len(result.virulence_genes) == 2
    
    # stx1 should map to Toxin and be high risk
    stx = next(g for g in result.virulence_genes if g.gene_name == "stx1")
    assert stx.category_display == "Toxin"
    assert stx.is_high_risk is True
    assert stx.identity_pct == 99.5
    
    # Check that pathogenicity profile was built
    assert result.pathogenicity_profile is not None
    assert result.pathogenicity_profile.total_vf_genes == 2
    assert "stx1" in result.pathogenicity_profile.high_risk_genes
    assert result.pathogenicity_profile.high_risk_count == 1
