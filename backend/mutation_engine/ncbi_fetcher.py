"""Dual-mode NCBI Reference Fetcher.

Mode A (Production): Requires a pre-downloaded reference bundle.
Mode B (Research/Dev): Fetches from NCBI and caches.
"""

import os
import shutil
import urllib.request
from pathlib import Path

# Mapping of common species to their standard RefSeq Accessions
SPECIES_TO_ACCESSION = {
    "escherichia coli": "NC_000913.3",
    "staphylococcus aureus": "NC_007795.1",
    "salmonella enterica": "NC_003197.2",
    "pseudomonas aeruginosa": "NC_002516.2",
    "klebsiella pneumoniae": "NC_016845.1"
}

def get_accession_for_species(species: str) -> str:
    """Resolve species name to a standard RefSeq accession."""
    if not species or species.lower() == "unknown":
        return "NC_000913.3" # Fallback to E. coli K-12
    
    clean_species = species.lower().strip()
    return SPECIES_TO_ACCESSION.get(clean_species, "NC_000913.3")

def fetch_reference(species: str, output_path: str | Path, mode: str = "B"):
    """
    Fetch the reference FASTA for the given species.
    
    Args:
        species: Species name
        output_path: Where to save the resulting reference.fasta
        mode: "A" for Production (requires bundled file), "B" for Dev (downloads from NCBI)
    """
    accession = get_accession_for_species(species)
    cache_dir = Path("/app/data/references") if os.path.exists("/app/data") else Path("data/references")
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    cached_file = cache_dir / f"{accession}.fasta"
    out_path = Path(output_path)
    
    if cached_file.exists():
        shutil.copy(cached_file, out_path)
        return
        
    if mode == "A":
        raise FileNotFoundError(
            f"Mode A (Production) requires pre-downloaded reference for {accession}. "
            f"File not found in {cached_file}"
        )
        
    # Mode B: Fetch from NCBI Entrez
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nucleotide&id={accession}&rettype=fasta&retmode=text"
    
    print(f"Downloading reference {accession} from NCBI...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'AMRPipeline/1.0'})
        with urllib.request.urlopen(req) as response, open(cached_file, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
            
        shutil.copy(cached_file, out_path)
        print(f"Successfully downloaded and cached {accession}")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch {accession} from NCBI: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python ncbi_fetcher.py <species> <output_fasta>")
        sys.exit(1)
    fetch_reference(sys.argv[1], sys.argv[2], mode=os.getenv("REFERENCE_MODE", "B"))
