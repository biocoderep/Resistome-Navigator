import requests
import json
import time

API_URL = "http://127.0.0.1:8000/api/v1/batches"

def run_test():
    print("Triggering Batch Upload Pipeline Test...")
    
    # 1. Use the real downloaded E. coli FASTA
    files = []
    fasta_path = "data/ecoli_k12.fasta"
    try:
        with open(fasta_path, "rb") as f:
            content = f.read()
            files.append(("files", ("ecoli_k12.fasta", content, "application/octet-stream")))
    except FileNotFoundError:
        print(f"Could not find {fasta_path}. Ensure it exists!")
        return

        
    data = {
        "project_id": "123e4567-e89b-12d3-a456-426614174000",
        "batch_name": "Test Publication Pipeline Batch"
    }

    # 2. Upload to FastAPI
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
    
    # 3. Poll for status
    print(f"\nPolling status for Batch {batch_id}...")
    while True:
        status_res = requests.get(f"{API_URL}/{batch_id}")
        if status_res.status_code == 200:
            status_data = status_res.json()
            state = status_data.get("status")
            completed = status_data.get("completed", 0)
            total = status_data.get("total_isolates", 1)
            print(f"   Status: {state} | Progress: {completed}/{total} isolates completed")
            
            if state in ["COMPLETED", "FAILED", "COHORT_FAILED", "PARTIAL_FAILED"]:
                break
        time.sleep(3)
        
    print("\nPipeline Execution Finished!")
    print("\nTo view the results in your new publication-ready dashboard, run:")
    print('Rscript -e "shiny::runApp(\'r_dashboard/app.R\', port=8080, launch.browser=TRUE)"')

if __name__ == "__main__":
    run_test()
