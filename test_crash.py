"""
Reproduce the EXACT Uvicorn crash scenario.
Runs in the main thread to see if the crash is threading-related.
"""
import asyncio
import sys
import faulthandler

faulthandler.enable()

from graph_builder import extract_and_store_graph
from utils import get_files_to_index
import os

repos_dir = os.path.join(os.path.dirname(__file__), "data", "repos")
dirs = [d for d in os.listdir(repos_dir) if os.path.isdir(os.path.join(repos_dir, d))]
repo_dir = os.path.join(repos_dir, dirs[-1])
files = get_files_to_index(repo_dir)
print(f"Using repo: {dirs[-1]} ({len(files)} files)", flush=True)

def main():
    for attempt in range(5):
        repo_id = f"stress_test_{attempt}"
        print(f"\n--- Attempt {attempt+1}/5 ---", flush=True)
        try:
            print(f"Running synchronously in main thread...", flush=True)
            extract_and_store_graph(repo_id, files)
            print(f"Attempt {attempt+1}: SUCCESS!", flush=True)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Attempt {attempt+1}: FAILED: {e}", flush=True)
            return
    
    print("\n=== ALL 5 ATTEMPTS PASSED ===", flush=True)

if __name__ == "__main__":
    main()
