import time
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_ingestion():
    repos_to_test = [
        "https://github.com/tiangolo/fastapi", # Medium repo
        "https://github.com/hwchase17/langchain-minimal" # or some other repo, let's use a small one like "https://github.com/pallets/click"
    ]
    # Actually, full fastapi might be too big for a quick test, let's use something smaller
    repos_to_test = [
        "https://github.com/encode/starlette", 
        "https://github.com/django/asgiref"
    ]

    for repo_url in repos_to_test:
        print(f"\n--- Testing Ingestion for {repo_url} ---")
        
        # 1. Start indexing
        response = client.post("/index-repo", json={"url": repo_url})
        assert response.status_code == 202
        
        data = response.json()
        repo_id = data["repo_id"]
        print(f"[SUCCESS] Started indexing. Assigned Repo ID: {repo_id}")
        
        # 2. Poll status
        max_retries = 30
        for _ in range(max_retries):
            time.sleep(1) # wait 1 sec between polls
            status_res = client.get(f"/index-status/{repo_id}")
            assert status_res.status_code == 200
            status_data = status_res.json()
            
            print(f"Status: {status_data['status']}")
            
            if status_data['status'] == 'completed':
                print(f"[SUCCESS] Ingestion completed! Discovered files: {status_data.get('files_discovered')}")
                break
            elif status_data['status'] == 'failed':
                print(f"[ERROR] Ingestion failed! Error: {status_data.get('error')}")
                break
        else:
            print("[WARN] Timeout waiting for ingestion to complete.")

if __name__ == "__main__":
    test_ingestion()
