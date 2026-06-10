from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import os

app = FastAPI(title="AMR Platform MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import UploadFile, File, Form, BackgroundTasks
import asyncio

# Mock Data Routes for Frontend Dev
@app.post("/api/v1/samples/upload")
def upload_sample(file: UploadFile = File(...), isolate_name: str = Form(default="Test Isolate")):
    return {"id": "mock-sample-id", "isolate_name": isolate_name, "status": "UPLOADED"}

@app.post("/api/v1/analysis/run-full")
def run_full(payload: dict):
    # Simulates returning a job ID
    return {"id": "mock-job-id", "status": "QUEUED"}


@app.get("/api/v1/analysis/cohort")
def get_cohort():
    import os
    import json
    path = "e:/AMR_platform/AMR_vetgenomehub/backend/cohort_mock.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {"cohort": []}

@app.get("/api/v1/analytics/dim-reduction")
def get_dim_reduction(method: str = "umap"):
    from reporting.analytics import compute_dim_reduction
    return {"data": compute_dim_reduction(method)}

@app.get("/api/v1/analytics/network")
def get_network():
    from reporting.analytics import compute_cooccurrence_network
    return compute_cooccurrence_network()

@app.get("/api/v1/analytics/mst")
def get_mst():
    from reporting.analytics import compute_mst
    return compute_mst()

from fastapi.responses import HTMLResponse
@app.get("/api/v1/analysis/{job_id}/circos", response_class=HTMLResponse)
def get_circos(job_id: str):
    from reporting.genomic_plots import generate_circos_plot
    return generate_circos_plot(job_id)

# Mock Data Routes for Frontend Dev
@app.get("/api/v1/analysis/{job_id}")
def get_analysis(job_id: str):
    return {
        "amr_genes": [
            {
                "gene_name": "blaNDM-1",
                "gene_family": "NDM beta-lactamase",
                "antibiotic_class": "Carbapenem",
                "resistance_mechanism": "antibiotic inactivation",
                "confidence_score": 0.99,
                "hits": [
                    {"tool_name": "AMRFinderPlus", "identity": 100.0, "coverage": 100.0, "prediction": "Resistant"}
                ]
            },
            {
                "gene_name": "tet(A)",
                "gene_family": "tetracycline efflux pump",
                "antibiotic_class": "Tetracycline",
                "resistance_mechanism": "antibiotic efflux",
                "confidence_score": 0.95,
                "hits": [
                    {"tool_name": "CARD RGI", "identity": 99.5, "coverage": 100.0, "prediction": "Resistant"}
                ]
            },
            {
                "gene_name": "sul1",
                "gene_family": "sulfonamide resistant sul",
                "antibiotic_class": "Sulfonamide",
                "resistance_mechanism": "antibiotic target replacement",
                "confidence_score": 0.85,
                "hits": [
                    {"tool_name": "ResFinder", "identity": 100.0, "coverage": 100.0, "prediction": "Resistant"}
                ]
            }
        ],
        "phenotype_predictions": [
            {"drug": "Meropenem", "sir": "R", "evidence_name": "blaNDM-1", "confidence_score": 0.99, "explanation": "NDM-1 degrades carbapenems"},
            {"drug": "Imipenem", "sir": "R", "evidence_name": "blaNDM-1", "confidence_score": 0.99, "explanation": "NDM-1 degrades carbapenems"},
            {"drug": "Tetracycline", "sir": "R", "evidence_name": "tet(A)", "confidence_score": 0.95, "explanation": "tet(A) efflux pump active"},
            {"drug": "Sulfamethoxazole", "sir": "R", "evidence_name": "sul1", "confidence_score": 0.85, "explanation": "sul1 provides alternative DHPS"},
            {"drug": "Ciprofloxacin", "sir": "S", "evidence_name": "None", "confidence_score": 0.80, "explanation": "No fluoroquinolone resistance detected"},
            {"drug": "Gentamicin", "sir": "I", "evidence_name": "aac(3)-IVa (low confidence)", "confidence_score": 0.45, "explanation": "Partial hit for aminoglycoside acetyltransferase"},
            {"drug": "Colistin", "sir": "NOT_TESTABLE", "evidence_name": "None", "confidence_score": 0.0, "explanation": "No rule defined for this species"}
        ],
        "virulence_genes": [
            {"gene_name": "eae", "element_type": "adherence", "subclass": "intimin", "identity_pct": 100.0, "coverage_pct": 100.0},
            {"gene_name": "stx1A", "element_type": "toxin", "subclass": "Shiga toxin", "identity_pct": 99.8, "coverage_pct": 100.0}
        ]
    }

@app.get("/api/v1/samples")
def get_samples():
    return {
        "items": [
            {"id": "test-job-123", "name": "E.coli_ICU01", "status": "COMPLETED", "date": "2026-06-09"},
            {"id": "test-job-124", "name": "K.pneumoniae_W02", "status": "RUNNING", "date": "2026-06-09"},
            {"id": "test-job-125", "name": "S.aureus_MRSA", "status": "QUEUED", "date": "2026-06-08"}
        ]
    }

@app.get("/api/v1/samples/{sample_id}/validation")
def get_validation(sample_id: str):
    return {
        "status": "PASS",
        "validation": {
            "validation_status": "PASS",
            "assembly_metrics": {
                "n50": 150000,
                "contigs": 45,
                "total_length": 5100000,
                "gc_content": 50.5
            }
        }
    }

@app.get("/api/v1/analysis/cohort")
def get_cohort():
    path = "e:/AMR_platform/AMR_vetgenomehub/backend/cohort_mock.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {"cohort": []}
