"""Test script for real Docker-based databases."""

import sys
import shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.engines.amr_detection.wrappers import run_amrfinder, run_abricate

def main():
    print("=== Testing Real Database Docker Execution ===")
    
    root = Path(__file__).parent.parent.absolute()
    test_dir = root / "data" / "test_execution"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a mock FASTA file
    fasta_path = test_dir / "test_isolate.fasta"
    with open(fasta_path, "w") as f:
        # We use a short sequence. It won't find any real AMR genes, but it will prove the pipeline executes.
        f.write(">contig_1\nATGCGTACGTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGC\n")
    
    try:
        print("\n[1] Testing AMRFinderPlus...")
        amrfinder_out = run_amrfinder(fasta_path, test_dir)
        print(f" -> Output generated at {amrfinder_out}")
        with open(amrfinder_out, "r") as f:
            print(f" -> Output preview: {f.readline().strip()}")
            
        print("\n[2] Testing Abricate (CARD)...")
        abricate_out = run_abricate(fasta_path, test_dir, db="card")
        print(f" -> Output generated at {abricate_out}")
        with open(abricate_out, "r") as f:
            print(f" -> Output preview: {f.readline().strip()}")
            
        print("\n=== All execution tests passed! ===")
        
    except Exception as e:
        print(f"\n[ERROR] Execution failed: {e}")
        raise
    finally:
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)

if __name__ == "__main__":
    main()
