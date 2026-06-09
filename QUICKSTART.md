# AMR Platform - Quick Start Guide

## 🚀 Getting Started

This guide will help you set up and run the complete AMR detection pipeline.

---

## Prerequisites

- Docker & Docker Compose
- Python 3.10+
- Git
- ~50GB disk space for databases

---

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd AMR_vetgenomehub
```

### 2. Create Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start Infrastructure

```bash
docker-compose -f deploy/docker/docker-compose.yml up -d
```

This starts:
- PostgreSQL database (port 5432)
- Redis message broker (port 6379)
- Celery worker processes
- Celery Beat scheduler

### 5. Initialize Database

```bash
# Run migrations
alembic upgrade head

# Verify connection
python -c "from backend.database import engine; print('Database connected ✓')"
```

### 6. Start FastAPI Server

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Visit: http://localhost:8000/docs for interactive API documentation

---

## Running the Pipeline

### Option A: Using Nextflow (Recommended)

```bash
# Prepare sample CSV file
cat > samples.csv << EOF
sample_id,assembly_file,species
sample_001,./test_data/ecoli.fasta,Escherichia coli
sample_002,./test_data/staph.fasta,Staphylococcus aureus
EOF

# Run workflow
nextflow run nextflow/main.nf \
    --samples samples.csv \
    --output results/ \
    -profile docker
```

### Option B: Using FastAPI Directly

```bash
# Submit validation job
curl -X POST http://localhost:8000/api/v1/module1/validate \
  -F "sample_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "file_id=650e8400-e29b-41d4-a716-446655440001"

# Get results
curl http://localhost:8000/api/v1/module1/validate/assembly-uuid
```

### Option C: Using Python API

```python
from backend.genome_validator import GenomeValidationEngine
from backend.alignment import Bowtie2Aligner
from backend.amr_detection import CARDRGIDetector
from pathlib import Path

# Step 1: Validate genome
engine = GenomeValidationEngine()
validation_report = engine.validate(
    file_path=Path("assembly.fasta"),
    sample_id="sample-001",
    species="Escherichia coli"
)

if not validation_report.proceed_to_amr:
    print("Assembly failed validation")
    exit(1)

# Step 2: Run alignment
aligner = Bowtie2Aligner()
alignment_result = aligner.align(
    query_file=Path("assembly.fasta"),
    reference_db=Path("databases/card"),
    output_file=Path("alignment.bam")
)

# Step 3: Detect AMR genes
detector = CARDRGIDetector()
amr_result = detector.detect(
    assembly_file=Path("assembly.fasta"),
    output_dir=Path("results/")
)

print(f"Found {amr_result.total_amr_genes} AMR genes")
```

---

## Output Files

### Nextflow Results

```
results/
├── sample_001/
│   ├── validation/
│   │   └── validation_report.json
│   ├── alignment/
│   │   ├── alignment_report.json
│   │   └── alignment.bam
│   ├── amr_detection/
│   │   ├── rgi*.json
│   │   └── amrfinderplus*.tsv
│   ├── aggregation/
│   │   └── aggregated_results.json
│   └── reports/
│       ├── report.html
│       ├── report.json
│       └── report.tsv
└── .nextflow/
    ├── trace.txt
    ├── timeline.html
    └── report.html
```

### Report Contents

**report.json:**
```json
{
  "sample_id": "sample_001",
  "validation_status": "PASS",
  "quality_score": 87.4,
  "total_amr_genes": 3,
  "consensus_hits": [...]
}
```

**report.html:**
- Interactive dashboard
- Quality metrics
- AMR gene summary
- Resistance class breakdown

---

## Monitoring

### Celery Tasks

```bash
# View active tasks
celery -A backend.celery_app inspect active

# View task stats
celery -A backend.celery_app inspect stats

# Monitor in real-time with Flower
celery -A backend.celery_app flower
# Visit: http://localhost:5555
```

### Nextflow Execution

```bash
# View workflow status
nextflow log

# Generate execution report
nextflow log -f '${name} - ${status} - {duration} - {memory}'

# Draw execution DAG
nextflow dag nextflow/main.nf | dot -Tpng > dag.png
```

---

## Configuration

### Customize Workflow Parameters

```bash
nextflow run nextflow/main.nf \
    --samples samples.csv \
    --alignment_cpus 16 \
    --alignment_memory "32 GB" \
    --amr_tools "card_rgi,amrfinderplus" \
    -profile docker
```

### Celery Configuration

Edit `backend/celery_config.py`:
```python
# Adjust timeouts
task_time_limit = 60 * 60  # 1 hour
task_soft_time_limit = 55 * 60  # 55 min

# Adjust worker concurrency
worker_concurrency = 4
```

---

## Troubleshooting

### Problem: Redis connection refused

```bash
# Check Redis status
docker-compose ps

# Restart Redis
docker-compose restart redis

# Check logs
docker-compose logs redis
```

### Problem: Celery worker not running

```bash
# Check worker status
celery -A backend.celery_app inspect active

# View worker logs
docker-compose logs celery_worker

# Restart workers
docker-compose restart celery_worker
```

### Problem: Database migration failed

```bash
# Check current version
alembic current

# View migrations
alembic history

# Rollback
alembic downgrade -1

# Retry
alembic upgrade head
```

### Problem: Nextflow workflow failed

```bash
# Check error messages
cat .nextflow/log

# Clean and retry
rm -rf .nextflow/work
nextflow run nextflow/main.nf --samples samples.csv -profile docker
```

---

## Testing

### Run Unit Tests

```bash
pytest backend/genome_validator/tests/test_genome_validator.py -v
```

### Run Integration Tests

```bash
# Create test data
mkdir -p test_data

# Run workflow with test profile
nextflow run nextflow/main.nf \
    -profile test \
    -with-trace \
    -with-report
```

---

## Development

### Directory Structure

```
AMR_vetgenomehub/
├── backend/                          # Backend Python code
│   ├── main.py                      # FastAPI application
│   ├── celery_app.py                # Celery initialization
│   ├── celery_config.py             # Celery configuration
│   ├── genome_validator/            # Validation service
│   ├── alignment/                   # Alignment service
│   ├── amr_detection/               # AMR detection service
│   ├── api/                         # API routes
│   ├── models/                      # Database models
│   ├── database/                    # Database config
│   ├── tasks/                       # Celery tasks
│   └── schemas/                     # Pydantic schemas
├── nextflow/                         # Nextflow workflows
│   ├── main.nf                      # Main workflow
│   ├── nextflow.config              # Nextflow config
│   └── processes/                   # Process definitions
├── deploy/                           # Deployment configs
│   └── docker/
│       └── docker-compose.yml       # Container orchestration
├── docs/                             # Documentation
│   └── specifications/              # System specifications
├── alembic/                          # Database migrations
│   └── versions/                    # Migration scripts
└── requirements.txt                  # Python dependencies
```

### Adding a New Tool

#### 1. Alignment Tool

Create `backend/alignment/tool_name.py`:
```python
from backend.alignment.base import BaseAligner, AlignmentConfig, AlignmentResult

class CustomAligner(BaseAligner):
    def align(self, query_file, reference_db, output_file, **kwargs):
        # Implementation
        pass
    
    def parse_output(self, output_file):
        # Implementation
        pass
```

#### 2. AMR Detection Tool

Create `backend/amr_detection/tool_name.py`:
```python
from backend.amr_detection.base import BaseAMRDetector, AMRConfig, AMRDetectionResult

class CustomDetector(BaseAMRDetector):
    def detect(self, assembly_file, output_dir, **kwargs):
        # Implementation
        pass
    
    def parse_results(self, output_dir):
        # Implementation
        pass
```

### Running with Custom Tools

Update `nextflow/main.nf`:
```groovy
include { sequence_alignment } from "./processes/alignment.nf"

workflow {
    // Use custom aligner
    alignment_results = sequence_alignment(
        validation_results,
        custom_aligner="my_custom_aligner"
    )
}
```

---

## API Documentation

### Validate Genome

**Endpoint:** `POST /api/v1/module1/validate`

**Parameters:**
- `sample_id` (required) - UUID
- `file_id` (required) - UUID of uploaded file
- `species` (optional) - Species name (default: "Unknown")
- `config` (optional) - ValidationConfig JSON

**Response:**
```json
{
  "status": "success",
  "data": {
    "sample_id": "...",
    "validation_status": "PASS",
    "quality_score": 87.4,
    "proceed_to_amr": true,
    "confidence_cap": "FULL"
  }
}
```

### Get Validation Results

**Endpoint:** `GET /api/v1/module1/validate/{assembly_id}`

**Response:**
```json
{
  "status": "success",
  "data": {
    "validation_status": "PASS",
    "quality_report": {...},
    "amr_detection": {...}
  }
}
```

---

## Performance Benchmarks

| Genome Size | Validation | Alignment | AMR Detection | Total |
|-------------|-----------|-----------|---------------|-------|
| 1 Mb | 5-10s | 10-20s | 40-80s | 60-110s |
| 5 Mb | 20-30s | 30-60s | 120-240s | 180-330s |
| 10 Mb | 40-60s | 60-120s | 240-480s | 360-660s |

**With Parallelization:** ~30% faster due to async processing

---

## Support

### Documentation
- [System Architecture](docs/specifications/01_System_Architecture.md)
- [Genome Validation Engine](docs/specifications/04_Genome_Validation_Engine.md)
- [Database Design](docs/specifications/02_Database_Design.md)
- [API Specification](docs/specifications/03_API_Specification.md)

### Resources
- [GitHub Issues](https://github.com/yourorg/amr-platform/issues)
- [Nextflow Community](https://nextflow.io/community)
- [Celery Documentation](https://docs.celeryproject.io/)

---

## License

See [LICENSE](LICENSE) file

---

**Last Updated:** 2026-06-09
