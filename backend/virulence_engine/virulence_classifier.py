"""Virulence category assignment - Module 1F v1.0.0"""

import json
from functools import lru_cache
from pathlib import Path
from .result_models import VirulenceRawHit

class VirulenceClassifier:
    def __init__(self, ontology_path: Path, gene_map_path: Path):
        self.ontology = json.loads(ontology_path.read_text(encoding="utf-8"))
        self.gene_map = json.loads(gene_map_path.read_text(encoding="utf-8"))
        self._cat_index = {c["code"]: c for c in self.ontology["categories"]}

    def classify(self, hit: VirulenceRawHit) -> dict:
        cat_code = self._lookup_category(hit.gene_name)
        cat = self._cat_index.get(cat_code, self._cat_index.get("unknown"))
        
        is_hr = (cat_code in self.ontology.get("high_risk_categories", [])
                 or hit.gene_name.lower() in [g.lower() for g in self.ontology.get("high_risk_genes", [])])
                 
        return {
            "category_code": cat_code,
            "category_display": cat["display"] if cat else "Unknown",
            "risk_weight": cat["risk_weight"] if cat else 0.10,
            "is_high_risk": is_hr
        }

    @lru_cache(maxsize=4096)
    def _lookup_category(self, gene_name: str) -> str:
        name = gene_name.lower()
        if name in self.gene_map:
            return self.gene_map[name]
            
        PREFIXES = {
            "fim": "adhesin", "pap": "adhesin", "stx": "toxin", "hly": "toxin",
            "inv": "invasin", "iuc": "iron_acquisition", "kps": "capsule",
            "spi": "secretion_system", "csg": "biofilm", "iro": "iron_acquisition"
        }
        return next((v for k, v in PREFIXES.items() if name.startswith(k)), "unknown")
