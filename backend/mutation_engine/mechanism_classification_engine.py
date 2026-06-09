"""Mechanism Classification Engine main entrypoint."""

import uuid
from typing import Dict, Any, List

from .mechanism_classifier import MechanismClassifier
from .mechanism_evidence import aggregate_mechanisms
from .drug_association import associate_drugs
from .mutation_prioritizer import rank_mutations

class MechanismClassificationEngine:
    """Main orchestrator for mechanism classification."""
    
    def __init__(self, job_id: str, config: Dict[str, Any], ontology_path: Any, aro_mapper: Any, kb: List[Dict]):
        self.job_id = job_id
        self.config = config
        self.classifier = MechanismClassifier(ontology_path, aro_mapper, kb)
        
    def run(self, genes: List[Any], mutations: List[Any], mappings: List[Any], progress_cb=None) -> Dict[str, Any]:
        """Run the mechanism classification pipeline."""
        if progress_cb: progress_cb(10, "CLASSIFYING_GENES_AND_MUTATIONS")
        
        mechanisms = aggregate_mechanisms(genes, mutations, mappings, self.classifier)
        
        if progress_cb: progress_cb(50, "ASSOCIATING_DRUGS")
        # In a real pipeline, we'd map these to ResistanceDeterminant objects first.
        # For the orchestrator stub, we pass an empty list or mapped determinants
        drug_associations = associate_drugs([])
        
        if progress_cb: progress_cb(80, "PRIORITIZING")
        # rank_mutations(...)
        
        if progress_cb: progress_cb(100, "COMPLETED")
        return {
            "mechanisms": mechanisms,
            "drug_associations": drug_associations
        }
