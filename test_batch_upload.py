import requests
import json
import time

API_URL = "http://127.0.0.1:8000/api/v1/batches"

def run_test():
    print("Triggering Batch Upload Pipeline Test...")
    
    # 1. Create 3 mock fasta files
    files = []
    for i in range(3):
        filename = f"isolate_00{i+1}.fasta"
        content = f">contig1\nATGCGTACGTAGCTAGCTAGCATCGATCGACTAGCTAGCTAGCTAGCTAGCTAGC{i}".encode('utf-8')
        files.append(("files", (filename, content, "application/octet-stream")))
        
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
            total = status_data.get("total_isolates", 3)
            print(f"   Status: {state} | Progress: {completed}/{total} isolates completed")
            
            if state in ["COMPLETED", "COHORT_FAILED", "PARTIAL_FAILED"]:
                break
        time.sleep(3)
        
    print("\n🎉 Pipeline Execution Finished!")
    print("\nTo view the results in your new publication-ready dashboard, run:")
    print('Rscript -e "shiny::runApp(\'r_dashboard/app.R\', port=8080, launch.browser=TRUE)"')

if __name__ == "__main__":
    run_test()
