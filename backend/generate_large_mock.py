import json
import random

DRUGS = ["Meropenem", "Imipenem", "Tetracycline", "Ciprofloxacin", "Sulfamethoxazole", "Colistin", "Gentamicin", "Ampicillin", "Cefotaxime", "Azithromycin", "Chloramphenicol"]
GENES = {
    "blaNDM-1": {"mech": "antibiotic inactivation", "class": "Carbapenem"},
    "blaKPC-2": {"mech": "antibiotic inactivation", "class": "Carbapenem"},
    "tet(A)": {"mech": "antibiotic efflux", "class": "Tetracycline"},
    "sul1": {"mech": "antibiotic target replacement", "class": "Sulfonamide"},
    "mcr-1": {"mech": "antibiotic target alteration", "class": "Polymyxin"},
    "aac(3)-IVa": {"mech": "antibiotic inactivation", "class": "Aminoglycoside"},
    "qnrS1": {"mech": "antibiotic target protection", "class": "Fluoroquinolone"},
    "blaTEM-1": {"mech": "antibiotic inactivation", "class": "Penicillin"},
    "blaCTX-M-15": {"mech": "antibiotic inactivation", "class": "Cephalosporin"},
    "mph(A)": {"mech": "antibiotic inactivation", "class": "Macrolide"}
}

def generate_isolate(idx):
    # Determine the "clade" or combination cluster
    # cluster 1: NDM + MCR + TEM
    # cluster 2: KPC + CTX-M
    # cluster 3: tet + sul + qnr
    r = random.random()
    if r < 0.3:
        g_names = ["blaNDM-1", "mcr-1", "blaTEM-1", "mph(A)"]
    elif r < 0.6:
        g_names = ["blaKPC-2", "blaCTX-M-15", "aac(3)-IVa"]
    else:
        g_names = ["tet(A)", "sul1", "qnrS1", "blaTEM-1"]
        
    # add some noise
    if random.random() > 0.5:
        g_names.append(random.choice(list(GENES.keys())))
        
    g_names = list(set(g_names))
    
    genes = []
    phenotypes = []
    
    for g in g_names:
        genes.append({
            "gene_name": g,
            "antibiotic_class": GENES[g]["class"],
            "resistance_mechanism": GENES[g]["mech"],
            "confidence_score": round(random.uniform(0.65, 1.0), 2),
            "hits": [
                {
                    "tool_name": "AMRFinderPlus", 
                    "identity": round(random.uniform(85, 100), 2), 
                    "coverage": round(random.uniform(90, 100), 2), 
                    "prediction": "Resistant"
                }
            ]
        })
        
    # generate phenotypes based on genes
    for d in DRUGS:
        # Simplistic mapping
        if d in ["Meropenem", "Imipenem"] and any("Carbapenem" in GENES[x]["class"] for x in g_names):
            sir = "R"
            ev = [x for x in g_names if GENES[x]["class"] == "Carbapenem"][0]
        elif d == "Tetracycline" and "tet(A)" in g_names:
            sir = "R"
            ev = "tet(A)"
        elif d == "Ciprofloxacin" and "qnrS1" in g_names:
            sir = "I"
            ev = "qnrS1"
        elif d == "Colistin" and "mcr-1" in g_names:
            sir = "R"
            ev = "mcr-1"
        elif d == "Cefotaxime" and "blaCTX-M-15" in g_names:
            sir = "R"
            ev = "blaCTX-M-15"
        else:
            sir = "S"
            ev = "None"
            
        phenotypes.append({
            "drug": d,
            "sir": sir,
            "evidence_name": ev,
            "confidence_score": 1.0,
            "explanation": "Mocked"
        })
        
    return {
        "isolate_id": f"ISO_{idx:03d}",
        "amr_genes": genes,
        "phenotype_predictions": phenotypes
    }

cohort = []
for i in range(1, 51):
    cohort.append(generate_isolate(i))

with open("e:/AMR_platform/AMR_vetgenomehub/backend/cohort_mock.json", "w") as f:
    json.dump({"cohort": cohort}, f, indent=2)

print("Generated large mock data with 50 isolates.")
