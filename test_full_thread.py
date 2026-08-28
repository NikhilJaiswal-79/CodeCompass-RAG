import time, threading
from graph_builder import extract_and_store_graph
from utils import get_files_to_index

def full_pipeline():
    try:
        files = get_files_to_index('data/repos/NikhilJaiswal-79-safestep-7f220bd3')
        print(f"[Thread] Starting full pipeline with {len(files)} files", flush=True)
        start = time.time()
        extract_and_store_graph('test_full_thread', files)
        elapsed = time.time() - start
        print(f"[Thread] COMPLETED in {elapsed:.3f}s", flush=True)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[Thread] EXCEPTION: {e}", flush=True)

t = threading.Thread(target=full_pipeline)
t.start()
t.join(timeout=60)
if t.is_alive():
    print("[Main] THREAD HUNG after 60s!", flush=True)
else:
    print("[Main] Thread completed successfully.", flush=True)
