"""Knowledgebase mutation mapper - Module 1D v1.0.0"""

from typing import List, Dict, Optional
from .result_models import AnnotatedVariant, MutationMapping, MutationClassification, MutationEffect

def map_mutation(variant: AnnotatedVariant, kb_entries: List[Dict]) -> MutationMapping:
    """Match annotated variant against knowledgebase entries."""
    gene = variant.raw_variant.gene_name
    pos = variant.raw_variant.protein_position
    alt_aa = variant.raw_variant.alt_amino_acid
    
    if variant.effect == MutationEffect.SILENT:
        return MutationMapping(classification=MutationClassification.SILENT)
    
    # Check if the gene is in the knowledgebase
    gene_in_kb = any(e.get("gene") == gene for e in kb_entries)
    if not gene_in_kb:
        return MutationMapping(classification=MutationClassification.UNKNOWN)
    
    # 1. Exact match: gene + position + alt AA
    exact = [e for e in kb_entries if e.get("gene") == gene and 
             e.get("protein_position") == pos and 
             e.get("alt_amino_acid") == alt_aa]
             
    if exact:
        return MutationMapping(
            classification=MutationClassification.KNOWN_RESISTANCE,
            kb_entry=exact[0]
        )
        
    # 2. Position match: same gene + same position, different alt AA
    same_pos = [e for e in kb_entries if e.get("gene") == gene and 
                e.get("protein_position") == pos]
                
    if same_pos:
        entry_copy = dict(same_pos[0])
        entry_copy["note"] = f"Different amino acid change at known resistance position {pos}"
        return MutationMapping(
            classification=MutationClassification.LIKELY_RESISTANCE,
            kb_entry=entry_copy
        )
        
    # 3. Gene in KB but position not recorded
    if variant.domain:
        return MutationMapping(classification=MutationClassification.NOVEL_IN_DOMAIN)
        
    return MutationMapping(classification=MutationClassification.NOVEL)
