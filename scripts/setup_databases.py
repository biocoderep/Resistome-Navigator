"""Download script for real world AMR databases via Docker."""

import subprocess
import os
from pathlib import Path

def run_cmd(cmd):
    print(f"Executing: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def main():
    print("=== Real Database Setup ===")
    
    root = Path(__file__).parent.parent.absolute()
    data_dir = root / "data" / "databases"
    
    amrfinder_db_dir = data_dir / "amrfinderplus"
    amrfinder_db_dir.mkdir(parents=True, exist_ok=True)
    
    amrfinder_img = "staphb/ncbi-amrfinderplus:latest"
    abricate_img = "staphb/abricate:latest"
    
    try:
        print("\n[1] Pulling AMRFinderPlus Docker Image...")
        run_cmd(f"docker pull {amrfinder_img}")
        
        print("\n[2] Downloading/Updating AMRFinderPlus Database...")
        # Mount the local directory and tell amrfinder to update into it
        local_path = str(amrfinder_db_dir)
        # Handle Windows paths in Docker volume mount
        if os.name == 'nt':
            # e:\path -> /e/path for Git Bash/MSYS, but for Windows Docker native, e:/path works
            local_path = local_path.replace("\\", "/")
            
        cmd = f'docker run --rm -v "{local_path}:/database" {amrfinder_img} amrfinder_update --database /database'
        run_cmd(cmd)
        
        print("\n[3] Pulling Abricate Docker Image (includes VFDB & ResFinder)...")
        run_cmd(f"docker pull {abricate_img}")
        
        print("\n=== Setup Complete! ===")
        print(f"Databases saved to: {data_dir}")
        
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Setup failed during command execution: {e}")
        raise

if __name__ == "__main__":
    main()
