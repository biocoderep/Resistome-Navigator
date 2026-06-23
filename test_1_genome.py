import requests
import json
import time

API_URL = "http://127.0.0.1:8000/api/v1/batches"

def run_test():
    print("Triggering Batch Upload Pipeline Test for 7 Genomes...")
    
    fasta_paths = [
        "data/uploads/597211e6-b6ac-4f36-b84e-1ee3866ad2a1/SRR11589112_consensus.fasta"
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
            print("Could not find {}. Ensure it exists!".format(path))
            return

        
    data = {
        "project_id": "123e4567-e89b-12d3-a456-426614174000",
        "batch_name": "Test 1 SRA Genome Batch",
        "species": "Acinetobacter baumannii"
    }

    try:
        response = requests.post(API_URL, files=files, data=data)
        response.raise_for_status()
        result = response.json()
        batch_id = result.get("batch_id")
        print("Successfully uploaded! Batch ID: {}".format(batch_id))
    except requests.exceptions.ConnectionError:
        print("Failed to connect to FastAPI. Is it running on port 8000?")
        return
    except requests.exceptions.HTTPError as e:
        print("HTTP Error: {}".format(e.response.status_code))
        print(e.response.text)
        return
    finally:
        for f in file_objs:
            f.close()
    
    print("\nPolling status for Batch {}...".format(batch_id))
    while True:
        status_res = requests.get("{}/{}".format(API_URL, batch_id))
        if status_res.status_code == 200:
            status_data = status_res.json()
            state = status_data.get("status")
            completed = status_data.get("completed", 0)
            total = status_data.get("total_isolates", 1)
            print("   Status: {} | Progress: {}/{} isolates completed".format(state, completed, total))
            
            if state in ["COMPLETED", "FAILED", "COHORT_FAILED", "PARTIAL_FAILED"]:
                break
        time.sleep(3)
        
    print("\nPipeline Execution Finished!")
    
    print("\nGetting per-sample status...")
    samples_res = requests.get("{}/{}".format(API_URL, batch_id))
    samples_data = samples_res.json()
    for s in samples_data.get("samples", []):
        print("Sample: {} - Status: {}".format(s.get('isolate_name'), s.get('status')))
        if s.get("status") == "FAILED":
            # fetch validation report
            print("   Reason for FAILED: Fetching validation report from DB/API...")
            
if __name__ == "__main__":
    run_test()
