"""Reference CDS loader for the mutation detection engine.

The mutation engine needs wild-type reference coding sequences (CDS), keyed by
gene name, to localise resistance genes in an assembly and to call variants
against. In production these should be *curated* reference CDS (e.g. from CARD /
PointFinder / NCBI). This module loads such a FASTA when present and, as a
runnable fallback, synthesises internally-consistent placeholder references
derived from the curated mutation knowledgebase so the pipeline never hard-fails
on a missing reference set.

Resolution order for :func:`get_reference_sequences`:
    1. Explicit ``fasta_path`` argument, if the file exists.
    2. The bundled ``data/reference_cds.fasta``, if present.
    3. KB-derived synthetic references (logged as a WARNING).

Only the standard library is used here so the loader has no third-party
dependency surface of its own.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_FASTA = Path(__file__).parent / "data" / "reference_cds.fasta"

# Representative (most-common E. coli) codon per 1-letter amino acid. Used only
# when synthesising placeholder references from the knowledgebase.
AA1_TO_CODON: Dict[str, str] = {
    "A": "GCA", "R": "CGT", "N": "AAC", "D": "GAC", "C": "TGC",
    "Q": "CAG", "E": "GAA", "G": "GGT", "H": "CAC", "I": "ATC",
    "L": "CTG", "K": "AAA", "M": "ATG", "F": "TTC", "P": "CCG",
    "S": "TCG", "T": "ACC", "W": "TGG", "Y": "TAC", "V": "GTG",
    "*": "TAA",
}

AA3_TO_1: Dict[str, str] = {
    "Ala": "A", "Arg": "R", "Asn": "N", "Asp": "D", "Cys": "C",
    "Gln": "Q", "Glu": "E", "Gly": "G", "His": "H", "Ile": "I",
    "Leu": "L", "Lys": "K", "Met": "M", "Phe": "F", "Pro": "P",
    "Ser": "S", "Thr": "T", "Trp": "W", "Tyr": "Y", "Val": "V",
    "Stop": "*",
}

FILLER_CODON = "GCA"  # Ala — neutral filler for non-annotated positions
START_CODON = "ATG"


def load_references_from_fasta(path: Path) -> Dict[str, str]:
    """Parse a (multi-record) FASTA into ``{gene_name: upper_sequence}``.

    The gene name is taken as the first whitespace-delimited token of each
    header line, so headers like ``>gyrA Escherichia coli K-12`` map to ``gyrA``.
    """
    references: Dict[str, str] = {}
    name: Optional[str] = None
    parts: List[str] = []

    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            if line.startswith(">"):
                if name is not None:
                    references[name] = "".join(parts).upper()
                name = line[1:].split()[0] if len(line) > 1 else ""
                parts = []
            else:
                parts.append(line)
        if name:
            references[name] = "".join(parts).upper()

    return references


def _codon_for_entry(entry: dict) -> Optional[str]:
    """Resolve the reference codon for a KB entry (explicit, else by ref AA)."""
    ref_codon = entry.get("ref_codon")
    if ref_codon and len(ref_codon) == 3:
        return ref_codon.upper()

    ref_aa = entry.get("ref_amino_acid")
    if not ref_aa:
        return None
    aa1 = AA3_TO_1.get(ref_aa, ref_aa if len(ref_aa) == 1 else None)
    if aa1 is None:
        return None
    return AA1_TO_CODON.get(aa1.upper())


def synthesize_references_from_kb(kb_entries: List[dict]) -> Dict[str, str]:
    """Build internally-consistent placeholder CDS from KB entries.

    For each protein-coding gene the CDS is constructed so that the codon at
    each annotated ``protein_position`` translates to the KB reference amino acid
    (or matches the KB ``ref_codon`` when provided), with neutral filler codons
    elsewhere and an ``ATG`` start. Non-coding loci (e.g. ``23S rRNA``) are
    skipped — they require dedicated nucleotide-level handling, not codon CDS.
    """
    by_gene: Dict[str, List[dict]] = {}
    for entry in kb_entries:
        gene = entry.get("gene")
        pos = entry.get("protein_position")
        if not gene or pos is None:
            continue
        if "rrna" in gene.lower() or "rna" in gene.lower():
            continue  # non-coding locus
        by_gene.setdefault(gene, []).append(entry)

    references: Dict[str, str] = {}
    for gene, entries in by_gene.items():
        max_pos = max(int(e["protein_position"]) for e in entries)
        n_codons = max(max_pos + 5, 30)
        codons = [FILLER_CODON] * n_codons
        codons[0] = START_CODON

        for entry in entries:
            idx = int(entry["protein_position"]) - 1
            if idx < 0 or idx >= n_codons:
                continue
            codon = _codon_for_entry(entry)
            if codon:
                codons[idx] = codon

        codons[0] = START_CODON  # keep a valid start even if position 1 annotated
        references[gene] = "".join(codons)

    return references


def get_reference_sequences(
    fasta_path: Optional[str | Path] = None,
    kb_entries: Optional[List[dict]] = None,
    species: Optional[str] = None
) -> Dict[str, str]:
    """Return reference CDS keyed by gene, using the dual-mode resolution order.

    Args:
        fasta_path: Optional explicit path to a curated reference FASTA.
        kb_entries: Ignored (legacy parameter).
        species: Optional species to dynamically fetch if no explicit FASTA provided.
    """
    candidates: List[Path] = []
    if fasta_path:
        candidates.append(Path(fasta_path))
    
    # Check default bundled fasta
    if DEFAULT_FASTA.exists():
        candidates.append(DEFAULT_FASTA)

    # Attempt to load local candidates
    for path in candidates:
        if path.exists():
            refs = load_references_from_fasta(path)
            if refs:
                logger.info("Loaded %d reference CDS from %s", len(refs), path)
                return refs

    # Dual-Mode dynamic fetch fallback
    import os
    from .ncbi_fetcher import fetch_reference, get_accession_for_species
    
    mode = os.getenv("REFERENCE_MODE", "B")
    accession = get_accession_for_species(species)
    cache_dir = Path("/app/data/references") if os.path.exists("/app/data") else Path("data/references")
    cached_file = cache_dir / f"{accession}.fasta"
    
    try:
        fetch_reference(species or "Unknown", cached_file, mode=mode)
        refs = load_references_from_fasta(cached_file)
        logger.info("Loaded %d reference CDS dynamically via mode %s from %s", len(refs), mode, cached_file)
        return refs
    except Exception as e:
        logger.error("Failed to load reference sequences: %s", e)
        # We explicitly fail rather than returning synthetic placeholder data
        return {}


__all__ = [
    "get_reference_sequences",
    "load_references_from_fasta",
]
