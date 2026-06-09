"""Mechanism classification engine - Module 1D v1.0.0"""

import json
from pathlib import Path
from typing import Dict, Any, List

class MechanismClassifier:
    """Classify AMR genes and mutations into mechanism classes."""
    
    def __init__(self, ontology_path: Path, aro_mapper: Any, kb: List[Dict]):
        self.ontology = json.loads(ontology_path.read_text()) if ontology_path.exists() else {"mechanism_classes": []}
        self.aro_mapper = aro_mapper
        self.kb = {e.get("entry_id"): e for e in kb if e.get("entry_id")}
        self._build_class_index()
        
    def _build_class_index(self):
        """Build fast lookup from ontology."""
        self.mech_index = {}
        for mc in self.ontology.get("mechanism_classes", []):
            self.mech_index[mc["code"]] = mc
            if "aro_term" in mc:
                self.mech_index[mc["aro_term"]] = mc
                
    def _build_result(self, code: str, source: str, confidence: float) -> Dict[str, Any]:
        """Build standard mechanism dict."""
        mc = self.mech_index.get(code, {"code": code, "display_name": code, "subclasses": []})
        return {
            "code": mc["code"],
            "name": mc.get("display_name", code),
            "source": source,
            "confidence": confidence
        }

    def _heuristic_classify(self, gene_name: str) -> Dict[str, Any]:
        """Fallback prefix-based classification."""
        gn = gene_name.lower()
        if gn.startswith("tet"):
            return self._build_result("efflux_pump", source="HEURISTIC", confidence=0.7)
        if gn.startswith("van"):
            return self._build_result("target_alteration", source="HEURISTIC", confidence=0.8)
        if gn.startswith("bla"):
            return self._build_result("antibiotic_inactivation", source="HEURISTIC", confidence=0.8)
        if gn.startswith("qnr"):
            return self._build_result("target_protection", source="HEURISTIC", confidence=0.8)
            
        return self._build_result("unknown", source="HEURISTIC", confidence=0.1)

    def classify_gene(self, gene: Any) -> Dict[str, Any]:
        """Classify an AMRGeneResult."""
        # Tier 1: ARO ontology
        if hasattr(gene, "aro_accession") and gene.aro_accession and self.aro_mapper:
            try:
                aro_mech = self.aro_mapper.lookup(gene.aro_accession)
                if aro_mech and aro_mech.get("resistance_mechanism"):
                    return self._build_result(aro_mech["resistance_mechanism"], source="ARO", confidence=0.95)
            except Exception:
                pass
                
        # Tier 2: pre-annotated mechanism from Module 1C
        if hasattr(gene, "mechanism_type") and gene.mechanism_type and gene.mechanism_type != "unknown":
            return self._build_result(gene.mechanism_type, source="AMR_DETECTION", confidence=0.85)
            
        # Tier 3: gene-name prefix heuristic
        name = getattr(gene, "gene_name", "")
        return self._heuristic_classify(name)

    def classify_mutation(self, mutation: Any, mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Classify a mutation based on its mapping."""
        # mapping could be a MutationMapping object
        # Since we use dataclass we access attribute
        kb_entry = getattr(mapping, "kb_entry", None)
        
        if kb_entry and kb_entry.get("mechanism"):
            conf = getattr(mapping, "confidence", 0.8)
            return self._build_result(kb_entry["mechanism"], source="KNOWLEDGEBASE", confidence=conf)
            
        return self._build_result("target_alteration", source="HEURISTIC", confidence=0.60)
