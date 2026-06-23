import json
import sys

with open(r'E:\AMR_platform\AMR_vetgenomehub\nextflow\.nextflow\work\aa\d1e5fb13085b5443f9d2698683dbb8\amr_detection_report.json') as f:
    r = json.load(f)

rgi_hits = r.get('rgi_results', {}).get('hits', [])
beta_lactams = [h['gene_name'] for h in rgi_hits if h['resistance_class'] == 'Beta-lactams']
print("Total RGI beta-lactams:", len(beta_lactams))
print(beta_lactams)
