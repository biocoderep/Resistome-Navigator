"""Unit tests for genome validation engine."""

import gzip
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest

from backend.genome_validator import GenomeValidationEngine, ValidationConfig


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def valid_fasta_file():
    """Create a temporary valid FASTA file for testing."""
    content = """>contig_1
ATGCGATCGTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGC
ATGCGATCGTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGC
>contig_2
GCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGC
GCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGC
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".fasta", delete=False) as f:
        f.write(content)
        f.flush()
        yield Path(f.name)
    
    # Cleanup
    Path(f.name).unlink()


@pytest.fixture
def fasta_with_short_contig():
    """Create FASTA with one contig below minimum length."""
    content = """>contig_1
ATGCGATCGTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGC
>contig_2_short
ATGC
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".fasta", delete=False) as f:
        f.write(content)
        f.flush()
        yield Path(f.name)
    
    Path(f.name).unlink()


@pytest.fixture
def fasta_with_invalid_chars():
    """Create FASTA with invalid nucleotide characters."""
    content = """>contig_1
ATGCGATCGTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCXYZ123
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".fasta", delete=False) as f:
        f.write(content)
        f.flush()
        yield Path(f.name)
    
    Path(f.name).unlink()


@pytest.fixture
def fasta_with_n_content():
    """Create FASTA with high N content."""
    content = """>contig_1
ATGCGATCGTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNN
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".fasta", delete=False) as f:
        f.write(content)
        f.flush()
        yield Path(f.name)
    
    Path(f.name).unlink()


@pytest.fixture
def gzipped_fasta_file():
    """Create a temporary gzipped FASTA file."""
    content = b""">contig_1
ATGCGATCGTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGC
ATGCGATCGTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGC
>contig_2
GCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGC
"""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".fasta.gz", delete=False) as f:
        with gzip.GzipFile(fileobj=f, mode="wb") as gz:
            gz.write(content)
        f.flush()
        yield Path(f.name)
    
    Path(f.name).unlink()


# ============================================================================
# INPUT VALIDATION TESTS
# ============================================================================


def test_valid_fasta_parsing(valid_fasta_file):
    """Test parsing a valid FASTA file."""
    engine = GenomeValidationEngine()
    report = engine.validate(
        file_path=valid_fasta_file,
        sample_id=str(uuid4()),
        assembly_id=str(uuid4()),
    )
    
    assert report.validation_status in ["PASS", "WARNING"]
    assert report.assembly_metrics is not None
    assert report.assembly_metrics.contig_count == 2
    assert report.assembly_metrics.total_length_bp > 0


def test_short_contig_warning(fasta_with_short_contig):
    """Test that short contigs generate warnings."""
    engine = GenomeValidationEngine(config=ValidationConfig(min_length_bp=200))
    report = engine.validate(
        file_path=fasta_with_short_contig,
        sample_id=str(uuid4()),
        assembly_id=str(uuid4()),
    )
    
    # Should have warnings about short contig
    assert len(report.warnings) > 0


def test_invalid_nucleotides(fasta_with_invalid_chars):
    """Test that invalid characters cause validation failure."""
    engine = GenomeValidationEngine()
    report = engine.validate(
        file_path=fasta_with_invalid_chars,
        sample_id=str(uuid4()),
        assembly_id=str(uuid4()),
    )
    
    # Should fail on invalid characters
    assert report.validation_status == "FAIL"
    assert len(report.errors) > 0


def test_high_n_content(fasta_with_n_content):
    """Test N% threshold detection."""
    engine = GenomeValidationEngine(
        config=ValidationConfig(
            n_warn_threshold=1.0,
            n_fail_threshold=5.0,
        )
    )
    report = engine.validate(
        file_path=fasta_with_n_content,
        sample_id=str(uuid4()),
        assembly_id=str(uuid4()),
    )
    
    # Should detect high N content
    assert report.ambiguity_report is not None
    assert report.ambiguity_report.n_percent > 5.0


def test_gzipped_fasta(gzipped_fasta_file):
    """Test parsing gzipped FASTA files."""
    engine = GenomeValidationEngine()
    report = engine.validate(
        file_path=gzipped_fasta_file,
        sample_id=str(uuid4()),
        assembly_id=str(uuid4()),
    )
    
    assert report.validation_status in ["PASS", "WARNING"]
    assert report.assembly_metrics is not None
    assert report.assembly_metrics.contig_count == 2


# ============================================================================
# ASSEMBLY METRICS TESTS
# ============================================================================


def test_metrics_computation(valid_fasta_file):
    """Test assembly metrics computation."""
    engine = GenomeValidationEngine()
    report = engine.validate(
        file_path=valid_fasta_file,
        sample_id=str(uuid4()),
        assembly_id=str(uuid4()),
    )
    
    metrics = report.assembly_metrics
    assert metrics is not None
    assert metrics.contig_count == 2
    assert metrics.n50_bp > 0
    assert metrics.gc_percent > 0
    assert metrics.gc_percent < 100


# ============================================================================
# QUALITY SCORING TESTS
# ============================================================================


def test_quality_score(valid_fasta_file):
    """Test quality score computation."""
    engine = GenomeValidationEngine()
    report = engine.validate(
        file_path=valid_fasta_file,
        sample_id=str(uuid4()),
        assembly_id=str(uuid4()),
    )
    
    assert report.quality_score >= 0.0
    assert report.quality_score <= 100.0
    assert report.quality_class in ["EXCELLENT", "GOOD", "ACCEPTABLE", "POOR", "FAILED"]


# ============================================================================
# DECISION ENGINE TESTS
# ============================================================================


def test_pass_decision(valid_fasta_file):
    """Test PASS decision for good assembly."""
    engine = GenomeValidationEngine()
    report = engine.validate(
        file_path=valid_fasta_file,
        sample_id=str(uuid4()),
        assembly_id=str(uuid4()),
    )
    
    # Good quality assembly should pass
    if report.quality_score >= 55:
        assert report.proceed_to_amr is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
