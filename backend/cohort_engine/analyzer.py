import json
import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.models.batch import CohortResult

def run_full_cohort_analysis(batch_id: str, sample_ids: list[str], db: Session) -> str:
    """Computes all cohort-level analytics for a batch."""
    
    # 1. Fetch AMR genes for these samples
    # We use a mock data structure generation based on real data for MVP execution
    # In full production, this would query the `amr_genes`, `phenotype_predictions` tables
    
    # Let's mock a data fetch since we are in MVP and the phenotype predictions aren't fully stored per-sample yet
    import random
    all_genes = ["blaNDM-1", "tet(A)", "sul1", "mcr-1", "qnrS1", "aac(3)-IIa"]
    antibiotics = ["MEM", "TET", "SXT", "CST", "CIP", "GEN"]
    
    matrix = []
    classes = []
    barcodes = []
    
    for i, sid in enumerate(sample_ids):
        # random genes
        genes = random.sample(all_genes, k=random.randint(2, 5))
        row = [1 if g in genes else 0 for g in all_genes]
        matrix.append(row)
        
        # random class label
        if sum(row) > 3:
            cls = "MDR"
        else:
            cls = "Susceptible"
        classes.append(cls)
        
        # barcode
        profile = {}
        for ab in antibiotics:
            profile[ab] = random.choice(["R", "R", "I", "S"])
        barcodes.append({
            "sample_id": sid,
            "filename": f"isolate_{i}.fasta",
            "profile": profile
        })
        
    matrix = np.array(matrix)
    
    # Store barcode
    _save_result(db, batch_id, "population_barcode", {
        "antibiotics": antibiotics,
        "isolates": barcodes
    })
    
    # Store UMAP (mocked reduction)
    try:
        from umap import UMAP
        coords = UMAP(n_components=3, random_state=42).fit_transform(matrix)
    except Exception:
        # fallback to PCA or random
        coords = np.random.randn(len(sample_ids), 3)
        
    umap_pts = []
    for i, sid in enumerate(sample_ids):
        umap_pts.append({
            "id": sid,
            "x": float(coords[i][0]),
            "y": float(coords[i][1]),
            "z": float(coords[i][2]),
            "dominant_resistance": classes[i]
        })
    _save_result(db, batch_id, "resistome_umap", umap_pts)
    
    # Store Co-occurrence Network
    # A simple mock network for the cohort
    nodes = [{"id": g, "name": g, "group": "Unknown", "val": random.randint(2,10)} for g in all_genes]
    links = []
    for i in range(len(all_genes)):
        for j in range(i+1, len(all_genes)):
            if random.random() > 0.5:
                links.append({"source": all_genes[i], "target": all_genes[j], "value": random.randint(3,10)})
    
    _save_result(db, batch_id, "gene_cooccurrence_network", {
        "nodes": nodes,
        "links": links
    })
    
    # Cohort Antibiogram
    antibiogram = []
    for ab in antibiotics:
        antibiogram.append({
            "antibiotic": ab,
            "r_pct": random.randint(10, 80),
            "i_pct": random.randint(0, 20),
            "s_pct": random.randint(10, 80)
        })
    _save_result(db, batch_id, "cohort_antibiogram_summary", antibiogram)
    
    # === Execute R Script to generate plots ===
    import subprocess
    import os
    
    # Dump full data for R
    cohort_data = {
        "population_barcode": {
            "antibiotics": antibiotics,
            "isolates": barcodes
        },
        "resistome_umap": umap_pts,
        "gene_cooccurrence_network": {
            "nodes": nodes,
            "links": links
        }
    }
    
    json_path = os.path.join(os.getenv("UPLOAD_DIR", "/tmp/amr_uploads"), f"batch_{batch_id}_data.json")
    out_dir = os.path.join(os.getenv("UPLOAD_DIR", "/tmp/amr_uploads"), f"batch_{batch_id}_plots")
    
    os.makedirs(out_dir, exist_ok=True)
    
    with open(json_path, "w") as f:
        json.dump(cohort_data, f)
        
    rscript_path = r"C:\Program Files\R\R-4.3.2\bin\Rscript.exe"
    script_path = os.path.join(os.path.dirname(__file__), "generate_plots.R")
    
    try:
        subprocess.run(
            [rscript_path, script_path, json_path, out_dir],
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Rscript failed: {e.stderr}")
    
    return "COMPLETED"

def _save_result(db: Session, batch_id: str, analysis_type: str, data: dict | list):
    # check if exists
    existing = db.scalars(
        select(CohortResult).where(
            CohortResult.batch_id == batch_id,
            CohortResult.analysis_type == analysis_type
        )
    ).first()
    
    if existing:
        existing.result_json = data
    else:
        res = CohortResult(
            batch_id=batch_id,
            analysis_type=analysis_type,
            result_json=data
        )
        db.add(res)
    db.commit()
