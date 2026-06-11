from typing import Any, Dict, List
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from scipy.cluster import hierarchy

from backend.database.session import get_session
from backend.models.sample import Sample
from backend.models.amr_gene import AmrGene

router = APIRouter(prefix="/surveillance", tags=["surveillance"])

@router.get("/pca")
def get_cohort_pca(
    batch_id: uuid.UUID | None = None,
    organism: str | None = None,
    db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Computes PCA on the resistome profiles.
    Returns: { "points": [...], "explainedVariance": [...] }
    """
    query = select(Sample.id, Sample.isolate_name, Sample.species, AmrGene.gene_name)\
        .join(AmrGene, Sample.id == AmrGene.sample_id)
        
    if batch_id:
        query = query.where(Sample.batch_id == str(batch_id))
    if organism:
        query = query.where(Sample.species == organism)
        
    results = db.execute(query).all()
    if not results:
        return {"points": [], "explainedVariance": [0, 0]}
        
    # Build dataframe
    df = pd.DataFrame(results, columns=["sample_id", "isolate_name", "species", "gene_name"])
    
    # Create presence/absence matrix (Rows: samples, Cols: genes)
    matrix = pd.crosstab(df['sample_id'], df['gene_name'])
    matrix = (matrix > 0).astype(int)
    
    if len(matrix) < 3 or matrix.shape[1] < 2:
        return {"points": [], "explainedVariance": [0, 0]}
    
    pca = PCA(n_components=2)
    components = pca.fit_transform(matrix)
    
    # Map back to sample info
    sample_to_species = df.drop_duplicates(subset=['sample_id']).set_index('sample_id')['species'].to_dict()
    
    points = []
    for idx, sample_id in enumerate(matrix.index):
        points.append({
            "sample_id": str(sample_id),
            "pc1": float(components[idx, 0]),
            "pc2": float(components[idx, 1]),
            "organism": sample_to_species.get(sample_id, "Unknown")
        })
        
    explained_var = [float(v * 100) for v in pca.explained_variance_ratio_]
    
    return {
        "points": points,
        "explainedVariance": explained_var
    }


@router.get("/clustermap")
def get_cohort_clustermap(
    batch_id: uuid.UUID | None = None,
    db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Computes hierarchical clustering linkage matrix for the clustermap.
    Returns: { "rowLabels": [], "colLabels": [], "matrix": [[]], "rowLinkage": [[]], "colLinkage": [[]] }
    """
    query = select(Sample.id, AmrGene.antibiotic_class)\
        .join(AmrGene, Sample.id == AmrGene.sample_id)
        
    if batch_id:
        query = query.where(Sample.batch_id == str(batch_id))
        
    results = db.execute(query).all()
    if not results:
        return {"rowLabels": [], "colLabels": [], "matrix": [], "rowLinkage": [], "colLinkage": []}
        
    df = pd.DataFrame(results, columns=["sample_id", "drug_class"])
    # Drop rows without drug class
    df = df.dropna(subset=['drug_class'])
    
    if df.empty:
        return {"rowLabels": [], "colLabels": [], "matrix": [], "rowLinkage": [], "colLinkage": []}

    # Rows: samples, Cols: drug classes
    matrix = pd.crosstab(df['sample_id'], df['drug_class'])
    matrix = (matrix > 0).astype(int)
    
    if len(matrix) < 2 or matrix.shape[1] < 2:
        return {
            "rowLabels": [str(x) for x in matrix.index],
            "colLabels": list(matrix.columns),
            "matrix": matrix.values.tolist(),
            "rowLinkage": [],
            "colLinkage": []
        }
        
    # Calculate scipy linkages
    row_linkage = hierarchy.linkage(matrix.values, method='ward')
    col_linkage = hierarchy.linkage(matrix.values.T, method='ward')
    
    # Format linkage arrays to list of lists (scipy outputs Nx4 arrays)
    row_linkage_list = row_linkage.tolist()
    col_linkage_list = col_linkage.tolist()
    
    return {
        "rowLabels": [str(x) for x in matrix.index],
        "colLabels": list(matrix.columns),
        "matrix": matrix.values.tolist(),
        "rowLinkage": row_linkage_list,
        "colLinkage": col_linkage_list
    }


@router.get("/rarefaction")
def get_cohort_rarefaction(
    batch_id: uuid.UUID | None = None,
    iterations: int = 10,
    db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Bootstrap rarefaction curve for unique genes.
    Returns: { "points": [{n_isolates, unique_genes_mean, ci_low, ci_high}] }
    """
    query = select(Sample.id, AmrGene.gene_name).join(AmrGene, Sample.id == AmrGene.sample_id)
    if batch_id:
        query = query.where(Sample.batch_id == str(batch_id))
        
    results = db.execute(query).all()
    if not results:
        return {"points": []}
        
    df = pd.DataFrame(results, columns=["sample_id", "gene_name"])
    samples = df['sample_id'].unique()
    n_samples = len(samples)
    
    if n_samples < 2:
        return {"points": []}
        
    points = []
    
    # For each subset size
    for k in range(1, n_samples + 1):
        counts = []
        # Bootstrap iterations
        for _ in range(iterations):
            sampled_ids = np.random.choice(samples, size=k, replace=False)
            sampled_genes = df[df['sample_id'].isin(sampled_ids)]['gene_name'].nunique()
            counts.append(sampled_genes)
            
        points.append({
            "n_isolates": k,
            "unique_genes_mean": float(np.mean(counts)),
            "ci_low": float(np.percentile(counts, 5)),
            "ci_high": float(np.percentile(counts, 95))
        })
        
    return {"points": points}
