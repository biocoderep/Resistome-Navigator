import json
import os

rules = []

def add_gene_rule(gene_fam, drug, drug_class, antibiotic_class, action, evidence, conf):
    rules.append({
        "rule_id": f"RULE_{gene_fam.replace(' ', '_').upper()}_{drug.upper()}",
        "rule_name": f"{gene_fam} -> {drug} {action}",
        "rule_type": "gene_family",
        "drug": drug,
        "drug_class": drug_class,
        "antibiotic_class": antibiotic_class,
        "condition": {
            "type": "gene_family_match",
            "gene_family": gene_fam,
            "hit_types": ["Perfect", "Strict"],
            "min_identity": 90.0,
            "min_coverage": 80.0
        },
        "action": action,
        "evidence_level": evidence,
        "confidence_weight": conf
    })

def add_mut_rule(gene, pos, aa, drug, drug_class, antibiotic_class, action):
    rules.append({
        "rule_id": f"RULE_MUT_{gene}_{pos}{aa}_{drug.upper()}",
        "rule_name": f"{gene} {pos}{aa} -> {drug} {action}",
        "rule_type": "mutation",
        "drug": drug,
        "drug_class": drug_class,
        "antibiotic_class": antibiotic_class,
        "condition": {
            "type": "mutation_exact",
            "gene": gene,
            "protein_position": pos,
            "alt_amino_acid": aa
        },
        "action": action,
        "evidence_level": 1,
        "confidence_weight": 0.95
    })

# Beta-lactams
add_gene_rule("CTX-M beta-lactamase", "ceftriaxone", "cephalosporin", "beta-lactam", "R", 1, 0.97)
add_gene_rule("CTX-M beta-lactamase", "cefotaxime", "cephalosporin", "beta-lactam", "R", 1, 0.97)
add_gene_rule("CTX-M beta-lactamase", "cefepime", "cephalosporin", "beta-lactam", "R", 1, 0.95)
add_gene_rule("KPC beta-lactamase", "meropenem", "carbapenem", "beta-lactam", "R", 1, 0.99)
add_gene_rule("KPC beta-lactamase", "imipenem", "carbapenem", "beta-lactam", "R", 1, 0.99)
add_gene_rule("NDM beta-lactamase", "meropenem", "carbapenem", "beta-lactam", "R", 1, 0.99)
add_gene_rule("NDM beta-lactamase", "imipenem", "carbapenem", "beta-lactam", "R", 1, 0.99)
add_gene_rule("OXA beta-lactamase", "amoxicillin", "penicillin", "beta-lactam", "R", 1, 0.90)
add_gene_rule("TEM beta-lactamase", "ampicillin", "penicillin", "beta-lactam", "R", 1, 0.90)
add_gene_rule("SHV beta-lactamase", "ampicillin", "penicillin", "beta-lactam", "R", 1, 0.90)
add_gene_rule("mecA", "oxacillin", "penicillin", "beta-lactam", "R", 1, 0.99)
add_gene_rule("mecA", "cefoxitin", "cephalosporin", "beta-lactam", "R", 1, 0.99)

# Aminoglycosides
add_gene_rule("aac(6')", "gentamicin", "aminoglycoside", "aminoglycoside", "R", 1, 0.95)
add_gene_rule("aac(6')", "tobramycin", "aminoglycoside", "aminoglycoside", "R", 1, 0.95)
add_gene_rule("aph(3')", "kanamycin", "aminoglycoside", "aminoglycoside", "R", 1, 0.95)
add_gene_rule("ant(2'')", "gentamicin", "aminoglycoside", "aminoglycoside", "R", 1, 0.95)

# Macrolides
add_gene_rule("erm", "erythromycin", "macrolide", "macrolide", "R", 1, 0.98)
add_gene_rule("erm", "azithromycin", "macrolide", "macrolide", "R", 1, 0.98)
add_gene_rule("mef", "erythromycin", "macrolide", "macrolide", "R", 1, 0.90)

# Tetracyclines
add_gene_rule("tet", "tetracycline", "tetracycline", "tetracycline", "R", 1, 0.95)
add_gene_rule("tet", "doxycycline", "tetracycline", "tetracycline", "R", 1, 0.95)

# Fluoroquinolones (Mutations)
add_mut_rule("gyrA", 83, "L", "ciprofloxacin", "fluoroquinolone", "fluoroquinolone", "R")
add_mut_rule("gyrA", 83, "I", "ciprofloxacin", "fluoroquinolone", "fluoroquinolone", "R")
add_mut_rule("gyrA", 87, "N", "ciprofloxacin", "fluoroquinolone", "fluoroquinolone", "I")
add_mut_rule("parC", 80, "I", "ciprofloxacin", "fluoroquinolone", "fluoroquinolone", "I")

# Sulfa/Trimethoprim
add_gene_rule("sul", "sulfamethoxazole", "sulfonamide", "folate pathway antagonist", "R", 1, 0.95)
add_gene_rule("dfr", "trimethoprim", "trimethoprim", "folate pathway antagonist", "R", 1, 0.95)

repo = {
    "schema_version": "1.0.0",
    "rules": rules
}

path = "e:/AMR_platform/AMR_vetgenomehub/backend/phenotype_engine/rules/rule_repository.json"
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w") as f:
    json.dump(repo, f, indent=4)

print(f"Generated {len(rules)} EUCAST rules.")
