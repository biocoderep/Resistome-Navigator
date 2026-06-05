# 2-Week AMR Platform — Beginner Solo Developer Plan

## The Strategy

Instead of building everything from scratch, we run the tools that already work
(CARD RGI, AMRFinderPlus) and wrap them in the simplest possible API.

**What you WILL have at the end of 2 weeks:**
- Upload a FASTA file via a web form or API call
- CARD RGI runs on it automatically
- AMRFinderPlus runs on it
- Results come back as JSON showing detected AMR genes
- A basic PDF/JSON report you can download
- Everything running in Docker so it works on any machine

**What you will NOT have (save for later):**
- Full authentication system
- PostgreSQL database (use SQLite for now — much simpler)
- Nextflow orchestration
- Mutation detection engine
- Phenotype prediction
- Virulence profiling
- Kubernetes / production deployment

You can add those later. Getting real science working first is the right call.

---

## Tech Stack (Simplified)

| Component | Tool | Why |
|-----------|------|-----|
| Backend | FastAPI (Python) | Simple, fast, good docs |
| Database | SQLite via SQLAlchemy | No server to set up |
| Task queue | Background tasks (FastAPI built-in) | No Redis/Celery needed yet |
| File storage | Local disk /data/ | No MinIO/S3 needed yet |
| AMR tools | CARD RGI + AMRFinderPlus (Docker) | Already built; just run them |
| Deployment | Docker Compose (3 containers) | Simple |

---

## Day-by-Day Plan

---

### WEEK 1 — Get the tools running

---

### Day 1 — Set up your environment (Monday)

**Goal: Python works, Docker works, you can run a test.**

Morning:
```
Install Python 3.12
  → https://www.python.org/downloads/

Install Docker Desktop
  → https://www.docker.com/products/docker-desktop/

Install VS Code
  → https://code.visualstudio.com/
  → Install Python extension
  → Install Docker extension
```

Afternoon:
```
Create your project folder:
  mkdir amr_platform
  cd amr_platform

Create virtual environment:
  python -m venv venv
  source venv/bin/activate        (Mac/Linux)
  venv\Scripts\activate           (Windows)

Install FastAPI:
  pip install fastapi uvicorn[standard]

Create your first file — backend/main.py:

  from fastapi import FastAPI
  app = FastAPI()

  @app.get("/")
  def hello():
      return {"message": "AMR Platform is running"}

Run it:
  uvicorn backend.main:app --reload

Open browser: http://localhost:8000
You should see: {"message": "AMR Platform is running"}
```

**✓ Day 1 done when:** Browser shows the JSON message.

---

### Day 2 — Project structure and file upload (Tuesday)

**Goal: Accept a FASTA file upload and save it to disk.**

```
Create this folder structure:
  amr_platform/
  ├── backend/
  │   ├── main.py
  │   ├── routers/
  │   │   └── samples.py
  │   └── utils/
  │       └── file_utils.py
  ├── data/
  │   ├── uploads/
  │   └── results/
  ├── requirements.txt
  └── docker-compose.yml
```

Install dependencies:
```
pip install python-multipart aiofiles sqlalchemy
pip freeze > requirements.txt
```

Write backend/routers/samples.py:
```python
import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path

router = APIRouter()
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/samples/upload")
async def upload_sample(file: UploadFile = File(...)):
    # Validate it looks like a FASTA file
    if not file.filename.endswith((".fasta", ".fa", ".fna", ".fasta.gz")):
        raise HTTPException(400, "File must be a FASTA file (.fasta, .fa, .fna)")

    # Save it with a unique ID
    sample_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{sample_id}.fasta"

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    return {
        "sample_id": sample_id,
        "filename": file.filename,
        "size_bytes": len(content),
        "status": "uploaded"
    }
```

Update backend/main.py:
```python
from fastapi import FastAPI
from backend.routers import samples

app = FastAPI(title="AMR Platform", version="0.1.0")
app.include_router(samples.router, prefix="/api/v1", tags=["samples"])

@app.get("/")
def health():
    return {"status": "ok", "message": "AMR Platform running"}
```

Test it:
```
# In one terminal:
uvicorn backend.main:app --reload

# Open http://localhost:8000/docs
# You will see Swagger UI
# Try the POST /api/v1/samples/upload endpoint
# Upload any .fasta file
```

**✓ Day 2 done when:** You can upload a FASTA file and see a sample_id returned.

---

### Day 3 — Simple database to track samples (Wednesday)

**Goal: Remember what samples were uploaded. Use SQLite — no server needed.**

Install:
```
pip install sqlalchemy
pip freeze > requirements.txt
```

Create backend/database.py:
```python
from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, Session
from datetime import datetime, timezone

engine = create_engine("sqlite:///data/amr_platform.db")

class Base(DeclarativeBase):
    pass

class Sample(Base):
    __tablename__ = "samples"

    id          = Column(String, primary_key=True)
    filename    = Column(String, nullable=False)
    file_path   = Column(String, nullable=False)
    status      = Column(String, default="UPLOADED")
    # UPLOADED → RUNNING → COMPLETED → FAILED
    created_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at= Column(DateTime, nullable=True)
    error       = Column(Text, nullable=True)

Base.metadata.create_all(engine)

def get_db():
    with Session(engine) as session:
        yield session
```

Update backend/routers/samples.py to save to database:
```python
import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from pathlib import Path
from backend.database import get_db, Sample

router = APIRouter()
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/samples/upload")
async def upload_sample(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith((".fasta", ".fa", ".fna")):
        raise HTTPException(400, "File must be a FASTA file")

    sample_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{sample_id}.fasta"

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Save to database
    sample = Sample(
        id=sample_id,
        filename=file.filename,
        file_path=str(file_path),
        status="UPLOADED"
    )
    db.add(sample)
    db.commit()

    return {
        "sample_id": sample_id,
        "filename": file.filename,
        "status": "UPLOADED"
    }

@router.get("/samples/{sample_id}")
def get_sample(sample_id: str, db: Session = Depends(get_db)):
    sample = db.get(Sample, sample_id)
    if not sample:
        raise HTTPException(404, "Sample not found")
    return {
        "sample_id": sample.id,
        "filename": sample.filename,
        "status": sample.status,
        "created_at": sample.created_at,
        "error": sample.error
    }

@router.get("/samples")
def list_samples(db: Session = Depends(get_db)):
    samples = db.query(Sample).all()
    return [{"sample_id": s.id, "filename": s.filename, "status": s.status} for s in samples]
```

**✓ Day 3 done when:** Upload a FASTA, then GET /samples shows it with status UPLOADED.

---

### Day 4 — Run CARD RGI in Docker (Thursday)

**Goal: Run CARD RGI on an uploaded FASTA and capture the output.**

This is the most important day. CARD RGI is the main AMR detection tool.

First, test CARD RGI manually:
```bash
# Pull the CARD RGI Docker image
docker pull finlaymaguire/card-rgi:latest

# Download a test E. coli FASTA (small one):
curl -o test_ecoli.fasta "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/005/845/GCF_000005845.2_ASM584v2/GCF_000005845.2_ASM584v2_genomic.fna.gz"
gunzip test_ecoli.fasta.gz

# Run CARD RGI manually first so you understand the output:
docker run --rm \
  -v $(pwd):/data \
  finlaymaguire/card-rgi:latest \
  rgi main \
    --input_sequence /data/test_ecoli.fasta \
    --output_file /data/rgi_output \
    --local --clean \
    --input_type contig

# Look at the output:
cat rgi_output.txt
```

Once that works, create backend/engines/card_runner.py:
```python
import subprocess
import json
import os
from pathlib import Path

RESULTS_DIR = Path("data/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def run_card_rgi(sample_id: str, fasta_path: str) -> dict:
    """
    Run CARD RGI on a FASTA file.
    Returns dict with detected genes or error info.
    """
    output_prefix = str(RESULTS_DIR / sample_id / "card_rgi")
    os.makedirs(RESULTS_DIR / sample_id, exist_ok=True)

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{Path(fasta_path).parent.absolute()}:/input",
        "-v", f"{(RESULTS_DIR / sample_id).absolute()}:/output",
        "finlaymaguire/card-rgi:latest",
        "rgi", "main",
        "--input_sequence", f"/input/{Path(fasta_path).name}",
        "--output_file", "/output/card_rgi",
        "--local", "--clean",
        "--input_type", "contig"
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour max
        )

        if result.returncode != 0:
            return {
                "status": "FAILED",
                "error": result.stderr,
                "genes": []
            }

        # Parse the output TSV
        output_file = RESULTS_DIR / sample_id / "card_rgi.txt"
        genes = parse_rgi_output(str(output_file))

        return {
            "status": "COMPLETED",
            "genes": genes,
            "tool": "CARD RGI"
        }

    except subprocess.TimeoutExpired:
        return {"status": "FAILED", "error": "Timeout after 1 hour", "genes": []}
    except Exception as e:
        return {"status": "FAILED", "error": str(e), "genes": []}


def parse_rgi_output(tsv_path: str) -> list:
    """Parse CARD RGI output TSV into list of gene dicts."""
    genes = []
    try:
        with open(tsv_path) as f:
            lines = f.readlines()
        if len(lines) < 2:
            return genes  # No hits

        headers = lines[0].strip().split("\t")
        for line in lines[1:]:
            values = line.strip().split("\t")
            row = dict(zip(headers, values))
            genes.append({
                "gene_name":    row.get("Best_Hit_ARO", "Unknown"),
                "aro_id":       row.get("ARO", ""),
                "drug_class":   row.get("Drug Class", ""),
                "mechanism":    row.get("Resistance Mechanism", ""),
                "hit_type":     row.get("Cut_Off", ""),   # Perfect/Strict/Loose
                "identity_pct": float(row.get("Best_Identities", 0) or 0),
                "coverage_pct": float(row.get("%Coverage", 0) or 0),
                "contig":       row.get("Contig", ""),
            })
    except FileNotFoundError:
        pass  # No output file = no hits found
    return genes
```

**✓ Day 4 done when:** You can run run_card_rgi() from Python and get a list of genes back.

---

### Day 5 — Connect upload to analysis (Friday — end of Week 1)

**Goal: Upload FASTA → automatically runs CARD RGI → results in database.**

Create backend/routers/analysis.py:
```python
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from backend.database import get_db, Sample
from backend.engines.card_runner import run_card_rgi
import json
from pathlib import Path

router = APIRouter()
RESULTS_DIR = Path("data/results")

def run_analysis_background(sample_id: str, fasta_path: str):
    """This runs in the background after the API responds."""
    from backend.database import engine, Sample
    from sqlalchemy.orm import Session

    with Session(engine) as db:
        sample = db.get(Sample, sample_id)
        if not sample:
            return

        # Update status to RUNNING
        sample.status = "RUNNING"
        db.commit()

        # Run CARD RGI
        card_result = run_card_rgi(sample_id, fasta_path)

        # Save results to file
        results_dir = RESULTS_DIR / sample_id
        results_dir.mkdir(parents=True, exist_ok=True)
        with open(results_dir / "results.json", "w") as f:
            json.dump(card_result, f, indent=2)

        # Update database
        if card_result["status"] == "COMPLETED":
            sample.status = "COMPLETED"
            sample.completed_at = datetime.now(timezone.utc)
        else:
            sample.status = "FAILED"
            sample.error = card_result.get("error", "Unknown error")
        db.commit()


@router.post("/samples/{sample_id}/run")
def run_analysis(
    sample_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    sample = db.get(Sample, sample_id)
    if not sample:
        raise HTTPException(404, "Sample not found")
    if sample.status == "RUNNING":
        raise HTTPException(400, "Analysis already running")

    # Start analysis in background (API responds immediately)
    background_tasks.add_task(
        run_analysis_background,
        sample_id,
        sample.file_path
    )

    return {
        "sample_id": sample_id,
        "status": "RUNNING",
        "message": "Analysis started. Poll GET /samples/{sample_id}/results to check progress."
    }


@router.get("/samples/{sample_id}/results")
def get_results(sample_id: str, db: Session = Depends(get_db)):
    sample = db.get(Sample, sample_id)
    if not sample:
        raise HTTPException(404, "Sample not found")

    if sample.status not in ("COMPLETED", "FAILED"):
        return {
            "sample_id": sample_id,
            "status": sample.status,
            "message": "Analysis still running. Try again in a minute."
        }

    if sample.status == "FAILED":
        return {
            "sample_id": sample_id,
            "status": "FAILED",
            "error": sample.error
        }

    # Load results from file
    results_file = RESULTS_DIR / sample_id / "results.json"
    if not results_file.exists():
        raise HTTPException(500, "Results file not found")

    with open(results_file) as f:
        results = json.load(f)

    return {
        "sample_id": sample_id,
        "status": "COMPLETED",
        "filename": sample.filename,
        "completed_at": sample.completed_at,
        "amr_genes_detected": len(results.get("genes", [])),
        "amr_genes": results.get("genes", []),
        "tool": "CARD RGI"
    }
```

Update main.py to include the new router:
```python
from fastapi import FastAPI
from backend.routers import samples, analysis

app = FastAPI(title="AMR Platform", version="0.1.0")
app.include_router(samples.router, prefix="/api/v1", tags=["samples"])
app.include_router(analysis.router, prefix="/api/v1", tags=["analysis"])

@app.get("/")
def health():
    return {"status": "ok"}
```

Test the full flow:
```
1. POST /api/v1/samples/upload      → upload test_ecoli.fasta → get sample_id
2. POST /api/v1/samples/{id}/run    → starts CARD RGI in background
3. GET  /api/v1/samples/{id}        → check status (RUNNING → COMPLETED)
4. GET  /api/v1/samples/{id}/results → see detected AMR genes
```

**✓ Week 1 done when:** You can upload a real FASTA, run analysis, and see AMR genes in the results.

---

### WEEK 2 — Make it usable

---

### Day 6 — Add AMRFinderPlus (Monday)

**Goal: Run a second tool for better coverage.**

Pull AMRFinderPlus Docker image:
```bash
docker pull ncbi/amrfinderplus:latest

# Test manually:
docker run --rm \
  -v $(pwd):/data \
  ncbi/amrfinderplus:latest \
  amrfinder --nucleotide /data/test_ecoli.fasta \
  --output /data/amrfinder_out.tsv
```

Create backend/engines/amrfinder_runner.py:
```python
import subprocess
from pathlib import Path

RESULTS_DIR = Path("data/results")

def run_amrfinder(sample_id: str, fasta_path: str) -> dict:
    output_file = RESULTS_DIR / sample_id / "amrfinder.tsv"
    (RESULTS_DIR / sample_id).mkdir(parents=True, exist_ok=True)

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{Path(fasta_path).parent.absolute()}:/input",
        "-v", f"{(RESULTS_DIR / sample_id).absolute()}:/output",
        "ncbi/amrfinderplus:latest",
        "amrfinder",
        "--nucleotide", f"/input/{Path(fasta_path).name}",
        "--output", "/output/amrfinder.tsv",
        "--plus"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        if result.returncode != 0:
            return {"status": "FAILED", "error": result.stderr, "genes": []}

        genes = parse_amrfinder_output(str(output_file))
        return {"status": "COMPLETED", "genes": genes, "tool": "AMRFinderPlus"}

    except Exception as e:
        return {"status": "FAILED", "error": str(e), "genes": []}


def parse_amrfinder_output(tsv_path: str) -> list:
    genes = []
    try:
        with open(tsv_path) as f:
            lines = f.readlines()
        if len(lines) < 2:
            return genes

        headers = lines[0].strip().split("\t")
        for line in lines[1:]:
            values = line.strip().split("\t")
            row = dict(zip(headers, values))
            if row.get("Element type") not in ("AMR",):
                continue
            genes.append({
                "gene_name":    row.get("Gene symbol", ""),
                "drug_class":   row.get("Drug class", ""),
                "identity_pct": float(row.get("% Identity to reference sequence", 0) or 0),
                "coverage_pct": float(row.get("% Coverage of reference sequence", 0) or 0),
                "contig":       row.get("Contig id", ""),
                "tool":         "AMRFinderPlus"
            })
    except FileNotFoundError:
        pass
    return genes
```

Update analysis.py to run both tools and merge results.

**✓ Day 6 done when:** Results show genes from both CARD and AMRFinderPlus.

---

### Day 7 — Simple results merging (Tuesday)

**Goal: Combine results from both tools, remove duplicates.**

Create backend/engines/result_merger.py:
```python
def merge_results(card_result: dict, amrfinder_result: dict) -> dict:
    """
    Merge AMR gene results from CARD and AMRFinderPlus.
    If same gene detected by both tools, keep the one with higher identity.
    """
    all_genes = {}

    for gene in card_result.get("genes", []):
        key = gene["gene_name"].lower()
        if key not in all_genes or gene["identity_pct"] > all_genes[key]["identity_pct"]:
            gene["supporting_tools"] = ["CARD"]
            all_genes[key] = gene

    for gene in amrfinder_result.get("genes", []):
        key = gene["gene_name"].lower()
        if key in all_genes:
            # Same gene found by both tools — increase confidence
            all_genes[key]["supporting_tools"].append("AMRFinderPlus")
            all_genes[key]["multi_tool_confirmed"] = True
        else:
            gene["supporting_tools"] = ["AMRFinderPlus"]
            gene["multi_tool_confirmed"] = False
            all_genes[key] = gene

    merged = list(all_genes.values())

    # Sort by number of supporting tools (most confirmed first)
    merged.sort(key=lambda g: len(g.get("supporting_tools", [])), reverse=True)

    return {
        "status": "COMPLETED",
        "total_genes": len(merged),
        "multi_tool_confirmed": sum(1 for g in merged if g.get("multi_tool_confirmed")),
        "genes": merged
    }
```

**✓ Day 7 done when:** Results endpoint shows genes with supporting_tools field.

---

### Day 8 — JSON and TSV report download (Wednesday)

**Goal: Download results as JSON or TSV file.**

Add to analysis.py:
```python
from fastapi.responses import FileResponse, StreamingResponse
import csv
import io

@router.get("/samples/{sample_id}/results/download")
def download_results(
    sample_id: str,
    format: str = "json",   # json or tsv
    db: Session = Depends(get_db)
):
    sample = db.get(Sample, sample_id)
    if not sample or sample.status != "COMPLETED":
        raise HTTPException(404, "Results not available")

    results_file = RESULTS_DIR / sample_id / "results.json"
    with open(results_file) as f:
        results = json.load(f)

    genes = results.get("genes", [])

    if format == "json":
        return results

    elif format == "tsv":
        output = io.StringIO()
        if genes:
            writer = csv.DictWriter(
                output,
                fieldnames=["gene_name", "drug_class", "mechanism",
                           "hit_type", "identity_pct", "coverage_pct",
                           "contig", "supporting_tools"],
                delimiter="\t"
            )
            writer.writeheader()
            for gene in genes:
                gene["supporting_tools"] = ";".join(gene.get("supporting_tools", []))
                writer.writerow({k: gene.get(k, "") for k in writer.fieldnames})

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/tab-separated-values",
            headers={"Content-Disposition": f"attachment; filename=amr_results_{sample_id}.tsv"}
        )
```

**✓ Day 8 done when:** GET /results/download?format=tsv returns a TSV file you can open in Excel.

---

### Day 9 — Simple HTML frontend (Thursday)

**Goal: A web page — no code required to use the platform.**

Create backend/static/index.html:
```html
<!DOCTYPE html>
<html>
<head>
    <title>AMR Platform</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; }
        h1 { color: #1a2744; }
        .card { border: 1px solid #ddd; padding: 20px; border-radius: 8px; margin: 20px 0; }
        button { background: #0c5460; color: white; padding: 10px 20px; border: none;
                 border-radius: 4px; cursor: pointer; font-size: 16px; }
        button:hover { background: #0a3f4a; }
        #status { padding: 10px; border-radius: 4px; margin: 10px 0; }
        .running { background: #fff3cd; }
        .completed { background: #d4edda; }
        .failed { background: #f8d7da; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th { background: #1a2744; color: white; padding: 8px; text-align: left; }
        td { padding: 8px; border-bottom: 1px solid #ddd; }
        tr:nth-child(even) { background: #f4f6f8; }
    </style>
</head>
<body>
    <h1>🧬 AMR Analysis Platform</h1>
    <p>Upload a bacterial genome assembly (FASTA format) to detect antimicrobial resistance genes.</p>

    <div class="card">
        <h2>Step 1: Upload Genome</h2>
        <input type="file" id="fastaFile" accept=".fasta,.fa,.fna">
        <br><br>
        <button onclick="uploadFile()">Upload FASTA</button>
        <div id="uploadStatus"></div>
    </div>

    <div class="card" id="runSection" style="display:none">
        <h2>Step 2: Run AMR Detection</h2>
        <p>Sample ID: <strong id="sampleIdDisplay"></strong></p>
        <button onclick="runAnalysis()">Run Analysis (CARD + AMRFinderPlus)</button>
        <div id="runStatus"></div>
    </div>

    <div class="card" id="resultsSection" style="display:none">
        <h2>Step 3: Results</h2>
        <div id="resultsSummary"></div>
        <button onclick="downloadTSV()">Download TSV</button>
        <button onclick="downloadJSON()" style="margin-left:10px; background:#276749">Download JSON</button>
        <div id="genesTable"></div>
    </div>

    <script>
        let currentSampleId = null;
        let pollInterval = null;

        async function uploadFile() {
            const file = document.getElementById('fastaFile').files[0];
            if (!file) { alert('Please select a FASTA file'); return; }

            const formData = new FormData();
            formData.append('file', file);

            document.getElementById('uploadStatus').innerHTML = 'Uploading...';

            const response = await fetch('/api/v1/samples/upload', {
                method: 'POST', body: formData
            });
            const data = await response.json();

            if (response.ok) {
                currentSampleId = data.sample_id;
                document.getElementById('uploadStatus').innerHTML =
                    `✓ Uploaded successfully`;
                document.getElementById('sampleIdDisplay').textContent = currentSampleId;
                document.getElementById('runSection').style.display = 'block';
            } else {
                document.getElementById('uploadStatus').innerHTML =
                    `✗ Error: ${data.detail}`;
            }
        }

        async function runAnalysis() {
            const response = await fetch(`/api/v1/samples/${currentSampleId}/run`, {
                method: 'POST'
            });
            const data = await response.json();
            document.getElementById('runStatus').innerHTML =
                '<div class="running">⏳ Analysis running... checking every 15 seconds</div>';

            pollInterval = setInterval(checkStatus, 15000);
        }

        async function checkStatus() {
            const response = await fetch(`/api/v1/samples/${currentSampleId}`);
            const data = await response.json();

            if (data.status === 'COMPLETED') {
                clearInterval(pollInterval);
                document.getElementById('runStatus').innerHTML =
                    '<div class="completed">✓ Analysis complete!</div>';
                loadResults();
            } else if (data.status === 'FAILED') {
                clearInterval(pollInterval);
                document.getElementById('runStatus').innerHTML =
                    `<div class="failed">✗ Failed: ${data.error}</div>`;
            }
        }

        async function loadResults() {
            const response = await fetch(`/api/v1/samples/${currentSampleId}/results`);
            const data = await response.json();

            document.getElementById('resultsSummary').innerHTML = `
                <p><strong>${data.amr_genes_detected}</strong> AMR genes detected</p>
            `;

            if (data.amr_genes && data.amr_genes.length > 0) {
                let html = '<table><tr><th>Gene</th><th>Drug Class</th><th>Mechanism</th><th>Identity %</th><th>Coverage %</th><th>Confirmed By</th></tr>';
                for (const gene of data.amr_genes) {
                    const tools = (gene.supporting_tools || []).join(', ');
                    html += `<tr>
                        <td><strong>${gene.gene_name}</strong></td>
                        <td>${gene.drug_class || '—'}</td>
                        <td>${gene.mechanism || '—'}</td>
                        <td>${gene.identity_pct ? gene.identity_pct.toFixed(1) + '%' : '—'}</td>
                        <td>${gene.coverage_pct ? gene.coverage_pct.toFixed(1) + '%' : '—'}</td>
                        <td>${tools}</td>
                    </tr>`;
                }
                html += '</table>';
                document.getElementById('genesTable').innerHTML = html;
            } else {
                document.getElementById('genesTable').innerHTML =
                    '<p>No AMR genes detected in this genome.</p>';
            }

            document.getElementById('resultsSection').style.display = 'block';
        }

        function downloadTSV() {
            window.location.href = `/api/v1/samples/${currentSampleId}/results/download?format=tsv`;
        }
        function downloadJSON() {
            window.location.href = `/api/v1/samples/${currentSampleId}/results/download?format=json`;
        }
    </script>
</body>
</html>
```

Update main.py to serve the HTML:
```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.routers import samples, analysis

app = FastAPI(title="AMR Platform", version="0.1.0")
app.mount("/static", StaticFiles(directory="backend/static"), name="static")
app.include_router(samples.router, prefix="/api/v1", tags=["samples"])
app.include_router(analysis.router, prefix="/api/v1", tags=["analysis"])

@app.get("/")
def index():
    return FileResponse("backend/static/index.html")
```

**✓ Day 9 done when:** Open http://localhost:8000 in browser, upload a FASTA, see results in a table.

---

### Day 10 — Docker Compose (Friday — end of Week 2 core)

**Goal: Everything runs with one command. Share with anyone.**

Create docker-compose.yml:
```yaml
version: "3.9"

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - PYTHONPATH=/app
    restart: unless-stopped

volumes:
  data:
```

Create Dockerfile:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install Docker CLI (to run CARD RGI containers from inside)
RUN apt-get update && apt-get install -y docker.io && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data/uploads data/results

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Test:
```bash
docker compose up --build
# Open http://localhost:8000
```

**✓ Day 10 done when:** `docker compose up` works and the web UI is accessible.

---

### Days 11–14 — Polish and Buffer

Use these days for whichever of these matter most to you:

**Day 11 — Better error handling and validation**
```
Add FASTA format validation (check first line starts with >)
Add file size limit (reject files > 500 MB)
Add better error messages when tools fail
Add timeout handling with user-friendly message
```

**Day 12 — Add ResFinder (third tool)**
```
Pull docker pull genomicepidemiology/resfinder
Add backend/engines/resfinder_runner.py
Update merger to include ResFinder results
```

**Day 13 — Simple confidence scoring**
```
Add confidence field to each gene result:
  HIGH   = detected by 2+ tools with identity > 95%
  MEDIUM = detected by 1 tool with identity > 90%
  LOW    = detected by 1 tool with identity < 90%
Display confidence in results table
```

**Day 14 — Final testing and cleanup**
```
Test with 5 different FASTA files (E. coli, S. aureus, K. pneumoniae, P. aeruginosa, MRSA)
Fix any bugs found
Update README.md with how to use it
Clean up any debug print statements
Tag release: git tag v0.1.0
```

---

## End of 2 Weeks — What You Have

| Feature | Status |
|---------|--------|
| Upload FASTA via web browser | ✓ Done |
| Upload FASTA via API (curl/Python) | ✓ Done |
| CARD RGI AMR detection | ✓ Done |
| AMRFinderPlus AMR detection | ✓ Done |
| ResFinder (if Day 12 done) | ✓ Done |
| Multi-tool result merging | ✓ Done |
| Results as JSON download | ✓ Done |
| Results as TSV (Excel) download | ✓ Done |
| Web UI with results table | ✓ Done |
| Docker Compose (one command deploy) | ✓ Done |
| SQLite database (sample history) | ✓ Done |

---

## What Comes After (Weeks 3–8)

Once this works, you can add the full platform piece by piece:

```
Week 3:  Mutation detection (Doc 7)
Week 4:  Phenotype prediction (Doc 8)
Week 5:  Virulence profiling (Doc 9)
Week 6:  Replace SQLite with PostgreSQL (Doc 2)
Week 7:  Replace background tasks with Celery + Redis (Doc 10)
Week 8:  Replace local Docker with Nextflow pipeline (Doc 10)
```

Each week adds one layer. Nothing breaks — you're building on top of what works.

---

## Folder Structure at End of Week 2

```
amr_platform/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── routers/
│   │   ├── samples.py
│   │   └── analysis.py
│   ├── engines/
│   │   ├── card_runner.py
│   │   ├── amrfinder_runner.py
│   │   ├── resfinder_runner.py   (Day 12)
│   │   └── result_merger.py
│   └── static/
│       └── index.html
├── data/
│   ├── uploads/
│   └── results/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## If You Get Stuck

**CARD RGI won't run:**
```bash
# Make sure Docker Desktop is running
docker info
# Re-pull the image
docker pull finlaymaguire/card-rgi:latest
```

**Permission error on Docker socket:**
```bash
# Linux only:
sudo chmod 666 /var/run/docker.sock
```

**Analysis stays RUNNING forever:**
```
# Check if the CARD container is actually running:
docker ps
# Check the error logs:
docker logs $(docker ps -lq)
```

**FASTA file too large / slow:**
```
# Use a smaller test genome first:
# E. coli K-12 (4.6 Mb) is a good standard test
# Download: https://www.ncbi.nlm.nih.gov/nuccore/U00096
```
