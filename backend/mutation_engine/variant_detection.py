"""Variant detection from pairwise alignment - Module 1D v1.0.0"""

from typing import List, Optional
from Bio.Seq import Seq

from .result_models import RawVariant, VariantType

STOP_CODONS = {"TAA", "TAG", "TGA"}

def _get_codon(seq: str, pos: int) -> Optional[str]:
    """Get codon given 1-based CDS position."""
    # pos is 1-based, so index is pos - 1
    idx = pos - 1
    codon_start = idx - (idx % 3)
    if codon_start + 3 <= len(seq):
        return seq[codon_start:codon_start+3].upper()
    return None

def _translate_codon(codon: Optional[str]) -> Optional[str]:
    """Translate DNA codon to 1-letter amino acid code."""
    if codon and len(codon) == 3 and "-" not in codon:
        try:
            return str(Seq(codon).translate())
        except Exception:
            return None
    return None

def _call_snp(q_char: str, r_char: str, cds_pos: int, gene_name: str, 
              query_aln: str, ref_aln: str, aln_idx: int) -> RawVariant:
    """Call a single nucleotide polymorphism."""
    protein_pos = (cds_pos - 1) // 3 + 1
    
    # Reconstruct the reference and query sequence without gaps to find codons
    ref_seq = ref_aln.replace("-", "")
    query_seq = query_aln.replace("-", "")
    
    # Calculate alignment quality in a window
    window_start = max(0, aln_idx - 10)
    window_end = min(len(query_aln), aln_idx + 10)
    matches = sum(1 for q, r in zip(query_aln[window_start:window_end], ref_aln[window_start:window_end]) if q == r and q != "-")
    window_len = window_end - window_start
    aln_quality = matches / window_len if window_len > 0 else 0.0
    
    codon_ref = _get_codon(ref_seq, cds_pos)
    # Finding query cds pos involves tracking gaps
    # It's easier to assume the same codon position if no indels, but we should find the exact query CDS pos
    query_cds_pos = len(query_aln[:aln_idx+1].replace("-", ""))
    codon_alt = _get_codon(query_seq, query_cds_pos)
    
    ref_aa = _translate_codon(codon_ref)
    alt_aa = _translate_codon(codon_alt)
    
    # If the codon resulted in a stop codon, update variant type
    vtype = VariantType.STOP_CODON if alt_aa == "*" else VariantType.SNP

    return RawVariant(
        gene_name=gene_name,
        cds_position=cds_pos,
        protein_position=protein_pos,
        ref_nucleotide=r_char.upper(),
        alt_nucleotide=q_char.upper(),
        ref_amino_acid=ref_aa,
        alt_amino_acid=alt_aa,
        variant_type=vtype,
        codon_ref=codon_ref,
        codon_alt=codon_alt,
        alignment_quality=aln_quality
    )

def _annotate_frameshifts(variants: List[RawVariant]) -> List[RawVariant]:
    """Post-process to detect frameshifts from indels."""
    frameshift_variants = []
    
    # Simple logic: group indels by protein position
    indel_counts = {}
    for v in variants:
        if v.variant_type in (VariantType.INSERTION, VariantType.DELETION):
            indel_counts[v.protein_position] = indel_counts.get(v.protein_position, 0) + 1
            
    for v in variants:
        if v.variant_type in (VariantType.INSERTION, VariantType.DELETION):
            if indel_counts[v.protein_position] % 3 != 0:
                v.variant_type = VariantType.FRAMESHIFT
                v.alt_amino_acid = "FS"
        frameshift_variants.append(v)
        
    return frameshift_variants

def call_variants(query_aln: str, ref_aln: str, gene_name: str) -> List[RawVariant]:
    """Call variants from a pairwise alignment (query vs reference)."""
    variants = []
    cds_pos = 0
    
    for i, (q_char, r_char) in enumerate(zip(query_aln, ref_aln)):
        if r_char != "-":
            cds_pos += 1
            
        if q_char == r_char:
            pass # match
        elif q_char == "-": # deletion in query
            protein_pos = (cds_pos - 1) // 3 + 1
            variants.append(RawVariant(
                gene_name=gene_name,
                cds_position=cds_pos,
                protein_position=protein_pos,
                ref_nucleotide=r_char.upper(),
                alt_nucleotide="-",
                ref_amino_acid=None,
                alt_amino_acid=None,
                variant_type=VariantType.DELETION,
                codon_ref=None,
                codon_alt=None,
                alignment_quality=0.5
            ))
        elif r_char == "-": # insertion in query
            protein_pos = (cds_pos - 1) // 3 + 1
            variants.append(RawVariant(
                gene_name=gene_name,
                cds_position=cds_pos,
                protein_position=protein_pos,
                ref_nucleotide="-",
                alt_nucleotide=q_char.upper(),
                ref_amino_acid=None,
                alt_amino_acid=None,
                variant_type=VariantType.INSERTION,
                codon_ref=None,
                codon_alt=None,
                alignment_quality=0.5
            ))
        else: # substitution (SNP)
            # Filter out Ns
            if q_char.upper() != "N" and r_char.upper() != "N":
                variants.append(_call_snp(q_char, r_char, cds_pos, gene_name, query_aln, ref_aln, i))
            
    return _annotate_frameshifts(variants)

def detect_stop_codons(coding_seq: str, gene_name: str) -> List[RawVariant]:
    """Scan translated CDS for premature stop codons."""
    variants = []
    
    for i in range(0, len(coding_seq) - 2, 3):
        codon = coding_seq[i:i+3].upper()
        aa_pos = i // 3 + 1
        
        # Stop codon found and it is not the very last expected codon
        if i < len(coding_seq) - 5 and codon in STOP_CODONS:
            variants.append(RawVariant(
                gene_name=gene_name, 
                cds_position=i+1,
                protein_position=aa_pos, 
                ref_nucleotide="",
                alt_nucleotide="*", 
                ref_amino_acid=None,
                alt_amino_acid="Stop", 
                variant_type=VariantType.STOP_CODON,
                codon_ref=None,
                codon_alt=codon,
                alignment_quality=1.0
            ))
            
    return variants
