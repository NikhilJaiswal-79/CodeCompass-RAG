import os
import shutil
import json
from agent import build_agent_graph
from chunker import parse_file_to_chunks
from database import get_or_create_collection
from embeddings import get_embedding
from rank_bm25 import BM25Okapi
import pickle

def setup_dummy_repo_for_agent(repo_id: str):
    print(f"--- Setting up dummy repo for {repo_id} ---")
    repos_dir = os.path.join(os.path.dirname(__file__), "data", "repos")
    os.makedirs(repos_dir, exist_ok=True)
    
    # Create rules
    rules = {
        "coding_standards": ["Always use descriptive variable names.", "Do not use global state."],
        "testing_requirements": ["Write unit tests using pytest."],
        "process_rules": []
    }
    with open(os.path.join(repos_dir, f"{repo_id}_rules.json"), "w") as f:
        json.dump(rules, f)
        
    # Create code
    py_content = """
def initialize_database(connection_string: str):
    # Initializes the main database connection
    # To see how we configure auth, look at setup_db_auth()
    pass

def setup_db_auth(token: str):
    # Configures authentication for the database
    # Critical security component
    pass
"""
    with open("dummy_agent.py", "w") as f:
        f.write(py_content)
        
    chunks = parse_file_to_chunks("dummy_agent.py")
    collection = get_or_create_collection(repo_id)
    
    documents = [c.content for c in chunks]
    metadatas = [{"name": c.name, "type": c.chunk_type, "file_path": "dummy_agent.py"} for c in chunks]
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    embeddings = [get_embedding(doc) for doc in documents]
    
    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )
    
    tokenized = [doc.lower().split() for doc in documents]
    bm25 = BM25Okapi(tokenized)
    
    with open(os.path.join(repos_dir, f"{repo_id}_bm25.pkl"), "wb") as f:
        pickle.dump(bm25, f)
    with open(os.path.join(repos_dir, f"{repo_id}_chunks.pkl"), "wb") as f:
        pickle.dump(metadatas, f)
        
    os.remove("dummy_agent.py")
    print(f"[SUCCESS] Ingestion complete.")

def run_test():
    test_repo_id = "test-agent-repo"
    setup_dummy_repo_for_agent(test_repo_id)
    
    graph = build_agent_graph()
    
    query = "How is the database initialized, and how is its authentication configured? Make sure to mention testing rules."
    print(f"\n--- Running Agent for Query: '{query}' ---\n")
    
    initial_state = {
        "repo_id": test_repo_id,
        "query": query,
        "sub_queries": [],
        "context_chunks": [],
        "rules": {},
        "iterations": 0,
        "final_answer": "",
        "next_action": ""
    }
    
    final_state = graph.invoke(initial_state)
    
    print("\n--- FINAL ANSWER ---\n")
    print(final_state["final_answer"])
    
if __name__ == "__main__":
    run_test()
