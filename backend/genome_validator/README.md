# Genome Validation Engine - MVP Implementation

## Overview

The Genome Validation Engine (GVE) is the mandatory first analytical gate of Module 1 of the AMR Platform. Every uploaded bacterial genome FASTA must pass through the GVE before any downstream AMR analysis is permitted.

## Implementation Status

**MVP Scope (Complete ✅)**

### Phase 1 (Green - MVP)
- ✅ Section 3: Input Validation (FASTA structure, IUPAC characters)
- ✅ Section 4: File Integrity (MD5/SHA256, gzip support)
- ✅ Section 5: Assembly Statistics (N50, GC%, contig count)
- ✅ Section 6: GC Content Analysis (per-contig GC, outlier detection)
- ✅ Section 7: Ambiguous Base Analysis (N%, N-run detection)
- ✅ Section 8: Contig Analysis (fragmentation classification)
- ✅ Section 15: Quality Scoring Engine (composite score 0-100)
- ✅ Section 16: PASS/WARNING/FAIL Decision Engine

### Phase 2 (Yellow - Stubs for future)
- 🟡 Section 9: Duplicate Contig Detection (MinHash, stubbed)
- 🟡 Section 10: Sequence Complexity (Shannon entropy, stubbed)
- 🟡 Section 11: K-mer Analysis (contamination detection, stubbed)
- 🟡 Section 13: Taxonomic Consistency (Mash species prediction, stubbed)
- 🟡 Section 14: Contamination Screening (risk aggregation, stubbed)

## Package Structure

```
backend/genome_validator/
├── __init__.py                  # Main package exports
├── models.py                    # Pydantic schemas for all reports
├── engine.py                    # Main orchestrator class
├── input_validator.py           # FASTA structure validation
├── integrity.py                 # MD5/SHA256 checksum computation
├── statistics.py                # Assembly metrics (N50, etc.)
├── gc_analysis.py              # GC content analysis
├── ambiguity.py                # N% and ambiguity code detection
├── contig_analysis.py          # Fragmentation and length distribution
├── duplicate_detector.py       # Duplicate detection (Phase 2 stub)
├── complexity.py               # Shannon entropy (Phase 2 stub)
├── kmer_analysis.py            # K-mer spectrum (Phase 2 stub)
├── genome_size.py              # Genome size validation
├── taxonomy.py                 # Taxonomic consistency (Phase 2 stub)
├── contamination.py            # Contamination screening (Phase 2 stub)
├── quality_scorer.py           # Composite quality score computation
├── decision_engine.py          # PASS/WARNING/FAIL determination
└── tests/
    └── test_genome_validator.py
```

## Usage

### Direct Python API

```python
from backend.genome_validator import GenomeValidationEngine, ValidationConfig
from pathlib import Path

# Initialize engine with optional config
config = ValidationConfig(
    min_length_bp=200_000,
    max_contig_count=2000,
    n_warn_threshold=1.0,
    n_fail_threshold=5.0,
)
engine = GenomeValidationEngine(config=config)

# Run validation
report = engine.validate(
    file_path=Path("/path/to/assembly.fasta"),
    sample_id="sample-uuid",
    assembly_id="assembly-uuid",
    species="Escherichia coli",
)

# Check results
print(f"Status: {report.validation_status}")
print(f"Quality: {report.quality_class} ({report.quality_score:.1f})")
print(f"Proceed to AMR: {report.proceed_to_amr}")
print(f"Confidence cap: {report.confidence_cap}")
```

### FastAPI Endpoint

```bash
# Submit validation job
curl -X POST http://localhost:8000/api/v1/module1/validate \
  -F "sample_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "file_id=650e8400-e29b-41d4-a716-446655440001"

# Get validation results
curl http://localhost:8000/api/v1/module1/validate/assembly-uuid
```

### Celery Async Task

```python
from backend.tasks import validate_genome_task

# Submit async task
result = validate_genome_task.delay(
    job_id="job-uuid",
    sample_id="sample-uuid",
    assembly_id="assembly-uuid",
    file_path="/path/to/assembly.fasta",
    species="Escherichia coli",
)

# Check status
status = result.status
```

## Validation Pipeline Steps

1. **Integrity Check** (5%) - Compute file checksums
2. **Input Validation** (10%) - Validate FASTA structure and characters
3. **Assembly Statistics** (20%) - Compute N50, contig counts, etc.
4. **GC Analysis** (30%) - Per-contig GC, outlier detection
5. **Ambiguity Analysis** (40%) - N% and N-run detection
6. **Contig Analysis** (45%) - Fragmentation classification
7. **Duplicate Detection** (50%) - MinHash similarity (Phase 2)
8. **Complexity Analysis** (58%) - Shannon entropy (Phase 2)
9. **K-mer Analysis** (65%) - K-mer spectrum (Phase 2)
10. **Genome Size Validation** (75%) - Size range checking
11. **Taxonomy Check** (80%) - Species consistency (Phase 2)
12. **Contamination Screening** (85%) - Risk aggregation (Phase 2)
13. **Quality Scoring** (90%) - Composite score computation
14. **Validation Decision** (95%) - PASS/WARNING/FAIL determination
15. **Report Generation** (100%) - Output file assembly

## Output Report

The validation engine produces a comprehensive `ValidationReport` containing:

### Master Report
- `validation_status` - PASS, WARNING, or FAIL
- `quality_score` - Numerical score (0-100)
- `quality_class` - EXCELLENT, GOOD, ACCEPTABLE, POOR, or FAILED
- `proceed_to_amr` - Boolean gate for downstream processing
- `confidence_cap` - FULL, MEDIUM, or LOW (affects downstream confidence scores)

### Sub-Reports
- `assembly_metrics` - N50, contig count, GC%, N%, etc.
- `gc_analysis` - Per-contig GC values and outliers
- `ambiguity_report` - N count, N-runs, other ambiguity codes
- `contig_report` - Fragmentation class, length distribution
- `duplicate_contig_report` - Exact and near-duplicate pairs
- `complexity_report` - Shannon entropy, homopolymers
- `kmer_report` - K-mer spectrum, coverage estimate
- `genome_size_report` - Size validation vs. expected range
- `taxonomy_report` - Species consistency check
- `contamination_report` - Risk level and signals
- `quality_score_detail` - Component breakdown of score

## Decision Rules

### PASS
- No critical FASTA errors
- Genome size within expected range (or user override)
- N% ≤ warning threshold
- Contamination risk = LOW_RISK
- Quality score ≥ 55
- No FAIL-level conditions

### WARNING
- No critical failures
- N% between warning and fail thresholds
- Contamination risk = MODERATE_RISK
- Quality score 40-54
- Assembly size outside expected range (minor deviation)

### FAIL
- FASTA parse error (no override)
- Genome too small (< 0.5 Mb, no override)
- Genome too large (> 15 Mb, admin override only)
- N% > fail threshold (user override available)
- Contamination risk = HIGH_RISK (user override available)
- Quality score < 40 (user override available)

## Database Integration

Validation results are persisted to PostgreSQL:

### Tables
- `assemblies` - One row per assembly file
- `assembly_metrics` - Computed metrics with quality scores
- `validation_reports` - Full validation report per run (supports re-runs)

### Columns Added to assembly_metrics
- `quality_score` - Composite score (0-100)
- `quality_classification` - EXCELLENT/GOOD/ACCEPTABLE/POOR/FAILED
- `confidence_cap` - FULL/MEDIUM/LOW
- `contamination_risk` - LOW_RISK/MODERATE_RISK/HIGH_RISK
- `gc_variance`, `gc_std_dev` - GC distribution metrics
- `taxonomy_status` - CONSISTENT/WARNING/MISMATCH

## Configuration

```python
ValidationConfig(
    min_length_bp=200_000,              # Minimum assembly size
    max_contig_count=2000,              # Maximum allowed contigs
    n_warn_threshold=1.0,               # N% warning threshold
    n_fail_threshold=5.0,               # N% fail threshold
    run_kmer_analysis=False,            # Phase 2 feature toggle
)
```

## Testing

Run the test suite:

```bash
pytest backend/genome_validator/tests/test_genome_validator.py -v
```

Test fixtures include:
- Valid multi-contig FASTA
- FASTA with short contigs
- FASTA with invalid characters
- FASTA with high N content
- Gzipped FASTA files

## Performance

Expected runtime for MVP validation:
- 1 Mb assembly: < 30 seconds
- 5 Mb assembly: < 120 seconds
- 15 Mb assembly: < 300 seconds

Phase 2 features (MinHash, k-mer analysis) may increase runtime by 30-60%.

## Future Enhancements (Phase 2+)

1. **Full Contamination Screening**
   - Bimodal GC distribution detection
   - K-mer frequency anomaly detection
   - Taxonomy mismatch with Mash

2. **Advanced Complexity Metrics**
   - Per-contig Shannon entropy tracking
   - Homopolymer region detection and flagging

3. **Duplicate Contig Resolution**
   - Exact and near-duplicate pair reporting
   - Recommendation for removal before AMR analysis

4. **Species-Specific Analysis**
   - ESKAPE pathogen-specific quality thresholds
   - NIAID priority pathogen special handling

5. **PDF Report Generation**
   - HTML template with embedded charts
   - GC distribution histogram
   - Contig length distribution
   - Quality score gauge visualization

## Dependencies

- `biopython >= 1.83` - FASTA parsing
- `numpy >= 1.26` - Numerical operations
- `scipy >= 1.12` - Statistical tests (Phase 2)
- `datasketch >= 1.6` - MinHash (Phase 2)
- `pydantic >= 2.6` - Schema validation
- `sqlalchemy >= 2.0` - Database ORM
- `pytest >= 8.0` - Testing framework

## Troubleshooting

### Common Issues

**Issue**: "INVALID_NUCLEOTIDE" error
- **Cause**: FASTA contains non-IUPAC characters (e.g., X, Y not for ambiguity)
- **Solution**: Filter or convert to standard IUPAC codes (A, T, G, C, N, R, Y, S, W, K, M, B, D, H, V)

**Issue**: "N_PERCENT_TOO_HIGH" warning
- **Cause**: Assembly contains > 1% ambiguous N bases
- **Solution**: Review assembly parameters or re-assemble with higher quality inputs

**Issue**: "CONTAMINATION_SUSPECTED" warning
- **Cause**: Per-contig GC% deviates > 3 SD from assembly mean
- **Solution**: Inspect outlier contigs; consider removing if from contaminant

**Issue**: High quality score but FAIL status
- **Cause**: Quality score alone doesn't determine pass/fail; other factors may cause FAIL
- **Solution**: Check fail_reasons list in validation report

## References

- [System Architecture Specification](../docs/specifications/01_System_Architecture.md)
- [Genome Validation Engine Specification](../docs/specifications/04_Genome_Validation_Engine.md)
- [NCBI Genome Assembly Statistics](https://www.ncbi.nlm.nih.gov/assembly/help/)
- [IUPAC Nucleotide Codes](https://www.bioinformatics.org/sms/iupac.html)
