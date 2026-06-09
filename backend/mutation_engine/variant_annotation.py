"""Variant annotation with HGVS-style notation - Module 1D v1.0.0"""

from Bio.Data import CodonTable
from .result_models import RawVariant, AnnotatedVariant, MutationEffect, VariantType

# Reverse mapping from 3-letter to 1-letter amino acid code
try:
    AA_3TO1 = {v: k for k, v in CodonTable.standard_dna_table.protein_letters_3to1.items()}
    # Add stop codon
    AA_3TO1["Stop"] = "*"
except AttributeError:
    # BioPython version compatibility
    AA_3TO1 = {
        'Ala': 'A', 'Arg': 'R', 'Asn': 'N', 'Asp': 'D', 'Cys': 'C',
        'Gln': 'Q', 'Glu': 'E', 'Gly': 'G', 'His': 'H', 'Ile': 'I',
        'Leu': 'L', 'Lys': 'K', 'Met': 'M', 'Phe': 'F', 'Pro': 'P',
        'Ser': 'S', 'Thr': 'T', 'Trp': 'W', 'Tyr': 'Y', 'Val': 'V',
        'Stop': '*'
    }

# Known resistance domains
RESISTANCE_DOMAINS = {
    "gyrA": {"QRDR": (67, 106)},
    "gyrB": {"QRDR": (426, 447)},
    "parC": {"QRDR": (78, 102)},
    "rpoB": {"RRDR": (507, 534)},
    "pbp2": {"Transpeptidase": (420, 475)},
    "mgrB": {"Sensor": (1, 63)}
}

def _get_domain(gene_name: str, protein_pos: int) -> str:
    """Check if mutation falls within a known resistance domain."""
    if gene_name in RESISTANCE_DOMAINS:
        for domain, (start, end) in RESISTANCE_DOMAINS[gene_name].items():
            if start <= protein_pos <= end:
                return domain
    return None

def annotate_variant(v: RawVariant, contig_id: str = None, start_pos: int = None) -> AnnotatedVariant:
    """Annotate variant with HGVS notation and domain info."""
    notation = ""
    hgvs_p = ""
    hgvs_c = f"c.{v.cds_position}{v.ref_nucleotide}>{v.alt_nucleotide}"
    effect = MutationEffect.SILENT
    
    if v.variant_type == VariantType.SNP:
        if v.ref_amino_acid != v.alt_amino_acid:
            # Missense
            notation = f"{v.gene_name} {v.ref_amino_acid}{v.protein_position}{v.alt_amino_acid}"
            
            # To 3 letter code for HGVS p. notation if available
            # Note: v.ref_amino_acid is 1-letter from BioPython translation
            # So we don't need AA_3TO1 dict for the 1-letter, we need the reverse:
            AA_1TO3 = {v2: k2 for k2, v2 in AA_3TO1.items()}
            ref_3 = AA_1TO3.get(v.ref_amino_acid, v.ref_amino_acid)
            alt_3 = AA_1TO3.get(v.alt_amino_acid, v.alt_amino_acid)
            
            hgvs_p = f"p.{ref_3}{v.protein_position}{alt_3}"
            effect = MutationEffect.MISSENSE
        else:
            # Silent
            notation = f"{v.gene_name} {v.ref_amino_acid}{v.protein_position}{v.alt_amino_acid}"
            hgvs_p = f"p.{v.ref_amino_acid}{v.protein_position}="
            effect = MutationEffect.SILENT
            
    elif v.variant_type == VariantType.STOP_CODON:
        notation = f"{v.gene_name} {v.ref_amino_acid}{v.protein_position}*" if v.ref_amino_acid else f"{v.gene_name} stop at {v.protein_position}"
        hgvs_p = f"p.{v.ref_amino_acid or ''}{v.protein_position}Ter"
        effect = MutationEffect.NONSENSE
        
    elif v.variant_type == VariantType.FRAMESHIFT:
        notation = f"{v.gene_name} frameshift at {v.protein_position}"
        hgvs_p = f"p.fs{v.protein_position}"
        hgvs_c = f"c.{v.cds_position}fs"
        effect = MutationEffect.FRAMESHIFT
        
    elif v.variant_type in (VariantType.INSERTION, VariantType.DELETION):
        notation = f"{v.gene_name} {v.variant_type.value.lower()} at {v.protein_position}"
        hgvs_p = f"p.indel{v.protein_position}"
        effect = MutationEffect.INFRAME_INDEL
        
    domain = _get_domain(v.gene_name, v.protein_position)
    
    return AnnotatedVariant(
        raw_variant=v,
        mutation_notation=notation,
        hgvs_protein=hgvs_p,
        hgvs_cdna=hgvs_c,
        effect=effect,
        domain=domain,
        contig_id=contig_id,
        start_pos=start_pos
    )
