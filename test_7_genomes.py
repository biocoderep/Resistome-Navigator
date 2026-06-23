import requests
import json
import time

API_URL = "http://127.0.0.1:8000/api/v1/batches"

def run_test():
    print("Triggering Batch Upload Pipeline Test for 7 Genomes...")
    
    fasta_paths = [
        "data/uploads/597211e6-b6ac-4f36-b84e-1ee3866ad2a1/SRR11589112_consensus.fasta",
        "data/uploads/cb273847-e880-44dd-bb78-3411b69471f1/SRR11589113_consensus.fasta",
        "data/uploads/92429c0e-ca38-44e6-a879-39c9c88954d5/SRR11589114_consensus.fasta",
        "data/uploads/a624bb59-fc12-427a-a89b-030c684d9fb4/SRR11589115_consensus.fasta",
        "data/uploads/8a03dcac-e7a8-45b5-a07f-fee73ebf39f9/SRR11589116_consensus.fasta",
        "data/uploads/c554438d-2515-49da-9880-16630cedfa07/SRR11589117_consensus.fasta",
        "data/uploads/9a266a7d-ec26-4723-b39a-3a0aa520630a/SRR11589118_consensus.fasta"
    ]
    
    files = []
    file_objs = []
    for path in fasta_paths:
        try:
            f = open(path, "rb")
            file_objs.append(f)
            filename = path.split("/")[-1]
            files.append(("files", (filename, f, "application/octet-stream")))
        except FileNotFoundError:
            print(f"Could not find {path}. Ensure it exists!")
            return

        
    data = {
        "project_id": "123e4567-e89b-12d3-a456-426614174000",
        "batch_name": "Test 7 SRA Genomes Batch",
        "species": "Acinetobacter baumannii"
    }

    try:
        response = requests.post(API_URL, files=files, data=data)
        response.raise_for_status()
        result = response.json()
        batch_id = result.get("batch_id")
        print(f"Successfully uploaded! Batch ID: {batch_id}")
    except requests.exceptions.ConnectionError:
        print("Failed to connect to FastAPI. Is it running on port 8000?")
        return
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code}")
        print(e.response.text)
        return
    finally:
        for f in file_objs:
            f.close()
    
    print(f"\nPolling status for Batch {batch_id}...")
    while True:
        status_res = requests.get(f"{API_URL}/{batch_id}")
        if status_res.status_code == 200:
            status_data = status_res.json()
            state = status_data.get("status")
            completed = status_data.get("completed", 0)
            total = status_data.get("total_isolates", 7)
            print(f"   Status: {state} | Progress: {completed}/{total} isolates completed")
            
            if state in ["COMPLETED", "FAILED", "COHORT_FAILED", "PARTIAL_FAILED"]:
                break
        time.sleep(3)
        
    print("\nPipeline Execution Finished!")
    
    print("\nGetting per-sample status...")
    samples_res = requests.get(f"{API_URL}/{batch_id}")
    samples_data = samples_res.json()
    for s in samples_data.get("samples", []):
        print(f"Sample: {s.get('isolate_name')} - Status: {s.get('status')}")
        if s.get("status") == "FAILED":
            # fetch validation report
            print(f"   Reason for FAILED: Fetching validation report from DB/API...")
            
if __name__ == "__main__":
    run_test()
