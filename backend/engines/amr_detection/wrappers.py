"""Docker Wrappers for AMR Detection Tools."""

import subprocess
import os
from pathlib import Path

def _get_docker_path(local_path: Path) -> str:
    """Convert a local Path to a docker-compatible path string for volumes."""
    path_str = str(local_path.absolute())
    if os.name == 'nt':
        return path_str.replace("\\", "/")
    return path_str

def run_amrfinder(fasta_path: Path, output_dir: Path) -> Path:
    """Run AMRFinderPlus against the provided FASTA file via Docker."""
    img = "staphb/ncbi-amrfinderplus:latest"
    
    # We find the database relative to the project root
    # Assuming this file is in backend/engines/amr_detection/wrappers.py
    root = Path(__file__).parent.parent.parent.parent.absolute()
    db_dir = root / "data" / "databases" / "amrfinderplus"
    
    out_file = output_dir / "amrfinder_results.tsv"
    
    # Mount fasta directory, output directory, and database directory
    fasta_vol = f"{_get_docker_path(fasta_path.parent)}:/data/input"
    out_vol = f"{_get_docker_path(output_dir)}:/data/output"
    db_vol = f"{_get_docker_path(db_dir)}:/database"
    
    fasta_name = fasta_path.name
    
    cmd = [
        "docker", "run", "--rm",
        "-v", fasta_vol,
        "-v", out_vol,
        "-v", db_vol,
        img,
        "amrfinder",
        "-n", f"/data/input/{fasta_name}",
        "--database", "/database/latest",
        "-o", f"/data/output/{out_file.name}",
        "--plus" # enable point mutations and virulence
    ]
    
    print(f"Executing AMRFinderPlus: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    return out_file

def run_abricate(fasta_path: Path, output_dir: Path, db: str = "card") -> Path:
    """Run Abricate against the provided FASTA file via Docker."""
    img = "staphb/abricate:latest"
    out_file = output_dir / f"abricate_{db}_results.tsv"
    
    fasta_vol = f"{_get_docker_path(fasta_path.parent)}:/data/input"
    out_vol = f"{_get_docker_path(output_dir)}:/data/output"
    
    fasta_name = fasta_path.name
    
    # Abricate prints to stdout, so we run via shell inside the container
    cmd = f'docker run --rm -v "{fasta_vol}" -v "{out_vol}" {img} sh -c "abricate --db {db} /data/input/{fasta_name} > /data/output/{out_file.name}"'
    
    print(f"Executing Abricate ({db}): {cmd}")
    subprocess.run(cmd, shell=True, check=True)
    return out_file
