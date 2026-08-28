import os
from graph_builder import extract_and_store_graph
from graph_queries import get_callers, get_callees, get_importers
import sqlite3

def run_test():
    test_repo_id = "test_graph_repo"
    
    # 1. Create a dummy Python file
    py_code = """
import requests
from utils import helper_func

class Database:
    def connect(self):
        helper_func()
        return "connected"

def fetch_data():
    db = Database()
    db.connect()
    requests.get("http://example.com")
"""
    with open("dummy_graph.py", "w") as f:
        f.write(py_code)
        
    # 2. Extract and store graph
    print("--- Extracting AST Graph ---")
    extract_and_store_graph(test_repo_id, ["dummy_graph.py"])
    
    # 3. Test queries
    print("\n--- Test: Who calls 'helper_func'? ---")
    callers = get_callers(test_repo_id, "helper_func")
    for c in callers:
        print(f"-> Called by {c['caller_type']} '{c['caller_name']}' on line {c['line_number']}")
        
    print("\n--- Test: Who calls 'connect'? ---")
    callers = get_callers(test_repo_id, "connect")
    for c in callers:
        print(f"-> Called by {c['caller_type']} '{c['caller_name']}' on line {c['line_number']}")

    print("\n--- Test: What does 'fetch_data' call? ---")
    callees = get_callees(test_repo_id, "fetch_data")
    for c in callees:
        print(f"-> Calls '{c['callee_name']}' on line {c['line_number']}")
        
    print("\n--- Test: Who imports 'requests'? ---")
    importers = get_importers(test_repo_id, "requests")
    for c in importers:
        print(f"-> Imported by {c['importer_type']} '{c['importer_name']}' on line {c['line_number']}")
        
    # Cleanup
    os.remove("dummy_graph.py")
    
if __name__ == "__main__":
    run_test()
