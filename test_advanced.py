import os
import shutil
from ingestion import process_repo
from agent import build_agent_graph

def setup_and_test():
    test_repo_id = "test-advanced-repo"
    test_repo_dir = os.path.join(os.path.dirname(__file__), "data", "repos", test_repo_id)
    
    # 1. Setup a dummy repo on disk so ingestion can process it fully
    os.makedirs(test_repo_dir, exist_ok=True)
    
    code = """
def initialize_database():
    # Sets up the primary database
    pass

def api_login(user):
    initialize_database()
    return "token"
"""
    with open(os.path.join(test_repo_dir, "db.py"), "w") as f:
        f.write(code)
        
    rules = """
    ## Rules
    - Always document the blast radius when modifying database functions.
    """
    with open(os.path.join(test_repo_dir, "CONTRIBUTING.md"), "w") as f:
        f.write(rules)
        
    print("--- 1. Ingesting Repo (Triggering Summarization & Graph Building) ---")
    import ingestion
    from unittest.mock import patch
    
    with patch('ingestion.clone_repo', return_value=True):
        process_repo("dummy_url", test_repo_id)
    
    print("\n--- 2. Running Advanced Agent ---")
    graph = build_agent_graph()
    
    query = "What happens if I change the initialize_database function? Are there any callers? Keep the rules in mind."
    print(f"Query: '{query}'")
    
    initial_state = {
        "repo_id": test_repo_id,
        "query": query,
        "sub_queries": [],
        "graph_targets": [],
        "hypothetical_code": "",
        "context_chunks": [],
        "graph_context": [],
        "rules": {},
        "iterations": 0,
        "final_answer": "",
        "next_action": ""
    }
    
    final_state = graph.invoke(initial_state)
    
    print("\n--- FINAL ANSWER ---\n")
    print(final_state["final_answer"])
    
    # Cleanup
    shutil.rmtree(test_repo_dir)

if __name__ == "__main__":
    setup_and_test()
