"""
Reproduce the exact Uvicorn background-thread scenario.
"""
import sqlite3, time, threading, sys
from chunker import get_language, extract_name
from tree_sitter import Parser
from graph_builder import _traverse_and_extract_edges, extract_and_store_graph
from graph_db import get_graph_db_connection
from utils import get_files_to_index

def simulate_background_task():
    """This runs in a thread, just like Uvicorn's BackgroundTasks."""
    try:
        print(f"[Thread] Started. Thread stack size: {threading.stack_size()}", flush=True)
        print(f"[Thread] Python recursion limit: {sys.getrecursionlimit()}", flush=True)
        
        files = get_files_to_index('data/repos/NikhilJaiswal-79-safestep-7f220bd3')
        print(f"[Thread] Found {len(files)} files", flush=True)
        
        repo_id = 'test_thread_dashboard'
        conn = get_graph_db_connection(repo_id)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM edges")
        cursor.execute("DELETE FROM nodes")
        
        for i, file_path in enumerate(files):
            if file_path.endswith(".py"):
                lang_name = "python"
            elif file_path.endswith(".js") or file_path.endswith(".jsx"):
                lang_name = "javascript"
            elif file_path.endswith(".ts") or file_path.endswith(".tsx"):
                lang_name = "typescript"
            else:
                continue
                
            language = get_language(lang_name)
            if not language:
                continue
                
            parser = Parser(language)
            try:
                with open(file_path, "rb") as f:
                    source_bytes = f.read()
            except Exception:
                continue
                
            tree = parser.parse(source_bytes)
            file_id = f"file_{file_path}"
            cursor.execute("INSERT OR IGNORE INTO nodes (id, name, type, file_path) VALUES (?, ?, ?, ?)",
                           (file_id, file_path.split('\\')[-1], "file", file_path))
            
            print(f"[Thread] Traversing {i}: {file_path.split(chr(92))[-1]}", flush=True)
            start = time.time()
            _traverse_and_extract_edges(tree.root_node, source_bytes, lang_name, file_id, file_path, cursor)
            elapsed = time.time() - start
            print(f"[Thread] Done traversing {i} in {elapsed:.3f}s", flush=True)
        
        conn.commit()
        print("[Thread] All files traversed successfully!", flush=True)
        conn.close()
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[Thread] EXCEPTION: {e}", flush=True)

# Run in a thread with default stack size (same as Uvicorn)
t = threading.Thread(target=simulate_background_task)
t.start()
t.join(timeout=30)

if t.is_alive():
    print("[Main] THREAD IS STILL ALIVE AFTER 30s - IT HUNG!", flush=True)
else:
    print("[Main] Thread completed successfully.", flush=True)
