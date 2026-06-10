import json
import os
import numpy as np

def load_cohort_data():
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cohort_mock.json")
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        data = json.load(f)
        return data.get("cohort", [])

def get_resistome_matrix(cohort):
    # Extract unique genes
    all_genes = set()
    for iso in cohort:
        for gene_obj in iso.get("amr_genes", []):
            all_genes.add(gene_obj.get("gene_name"))
    
    all_genes = sorted(list(all_genes))
    
    matrix = []
    ids = []
    classes = []
    
    for iso in cohort:
        ids.append(iso.get("id"))
        
        # Dominant drug class (just taking the most frequent for plotting colors)
        drug_counts = {}
        for pheno in iso.get("phenotype_predictions", []):
            if pheno.get("sir") == "R":
                drug_counts[pheno.get("drug")] = drug_counts.get(pheno.get("drug"), 0) + 1
        
        dom_class = max(drug_counts, key=drug_counts.get) if drug_counts else "Unknown"
        classes.append(dom_class)
        
        row = []
        iso_genes = {g.get("gene_name") for g in iso.get("amr_genes", [])}
        for g in all_genes:
            row.append(1 if g in iso_genes else 0)
        matrix.append(row)
        
    return np.array(matrix), ids, classes, all_genes

def compute_dim_reduction(method="pca"):
    cohort = load_cohort_data()
    if not cohort:
        return {"error": "No cohort data found"}
        
    matrix, ids, classes, _ = get_resistome_matrix(cohort)
    if len(matrix) == 0:
        return []
        
    # Standardize
    from sklearn.preprocessing import StandardScaler
    matrix_scaled = StandardScaler().fit_transform(matrix)
    
    if method == "umap":
        try:
            import umap
            reducer = umap.UMAP(n_neighbors=5, min_dist=0.3, n_components=3, random_state=42)
            coords = reducer.fit_transform(matrix_scaled)
        except ImportError:
            # Fallback to PCA if umap-learn not installed yet
            from sklearn.decomposition import PCA
            reducer = PCA(n_components=3)
            coords = reducer.fit_transform(matrix_scaled)
    else:
        from sklearn.decomposition import PCA
        reducer = PCA(n_components=3)
        coords = reducer.fit_transform(matrix_scaled)
        
    results = []
    for i, _id in enumerate(ids):
        results.append({
            "id": _id,
            "x": float(coords[i][0]),
            "y": float(coords[i][1]),
            "z": float(coords[i][2]),
            "dominant_resistance": classes[i]
        })
        
    return results

def compute_cooccurrence_network():
    cohort = load_cohort_data()
    if not cohort:
        return {"nodes": [], "links": []}
        
    # Map gene -> {class, mechanism}
    gene_info = {}
    
    co_matrix = {}
    gene_counts = {}
    
    for iso in cohort:
        genes_in_iso = []
        for g in iso.get("amr_genes", []):
            name = g.get("gene_name")
            if name not in gene_info:
                gene_info[name] = {
                    "class": g.get("antibiotic_class", "Unknown"),
                    "mechanism": g.get("resistance_mechanism", "Unknown")
                }
            genes_in_iso.append(name)
            gene_counts[name] = gene_counts.get(name, 0) + 1
            
        # Count co-occurrences
        for i in range(len(genes_in_iso)):
            for j in range(i + 1, len(genes_in_iso)):
                g1, g2 = sorted([genes_in_iso[i], genes_in_iso[j]])
                pair = f"{g1}||{g2}"
                co_matrix[pair] = co_matrix.get(pair, 0) + 1
                
    nodes = []
    for g, info in gene_info.items():
        nodes.append({
            "id": g,
            "name": g,
            "group": info["class"],
            "val": gene_counts.get(g, 1) * 2 # size
        })
        
    links = []
    for pair, count in co_matrix.items():
        if count >= 3: # threshold to reduce noise
            g1, g2 = pair.split("||")
            links.append({
                "source": g1,
                "target": g2,
                "value": count
            })
            
    return {"nodes": nodes, "links": links}

def compute_mst():
    cohort = load_cohort_data()
    if not cohort:
        return {"nodes": [], "links": []}
        
    matrix, ids, classes, _ = get_resistome_matrix(cohort)
    if len(matrix) == 0:
        return {"nodes": [], "links": []}
        
    from scipy.spatial.distance import pdist, squareform
    from scipy.sparse.csgraph import minimum_spanning_tree
    
    # Jaccard distance: 0 if identical resistome
    # Since minimum_spanning_tree expects distances, we use the distance matrix directly
    # To handle zero vectors which might cause NaNs in pdist, we add a tiny epsilon or handle it
    # We can use 'cityblock' (Manhattan) or 'euclidean' if 'jaccard' is problematic with all-zero rows
    try:
        distances = pdist(matrix, metric='jaccard')
    except Exception:
        distances = pdist(matrix, metric='euclidean')
        
    dist_matrix = squareform(distances)
    
    mst = minimum_spanning_tree(dist_matrix)
    mst_array = mst.toarray()
    
    nodes = []
    # Count identical isolates for node sizing if needed
    for i, _id in enumerate(ids):
        nodes.append({
            "id": _id,
            "name": _id,
            "group": classes[i],
            "val": 8
        })
        
    links = []
    n = len(ids)
    for i in range(n):
        for j in range(n):
            if mst_array[i, j] > 0:
                # Value for links usually indicates strength, inverse of distance
                weight = max(0.1, 1.0 - float(mst_array[i, j]))
                links.append({
                    "source": ids[i],
                    "target": ids[j],
                    "value": weight,
                    "distance": float(mst_array[i, j])
                })
                
    return {"nodes": nodes, "links": links}

