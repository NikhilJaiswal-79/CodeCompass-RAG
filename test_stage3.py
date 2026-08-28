import os
from chunker import parse_file_to_chunks
from embeddings import get_embedding
from retrieval import retrieve_hybrid
from database import get_or_create_collection
from rank_bm25 import BM25Okapi
import pickle

def setup_dummy_repo(repo_id: str):
    print(f"--- Setting up dummy repo for {repo_id} ---")
    py_content = """
class Router:
    def route_query(self, query: str):
        \"\"\"Determines the intent of a query and routes it to the appropriate subsystem.\"\"\"
        if "how" in query:
            return "semantic"
        return "keyword"

def fetchUserById(user_id: int):
    # This is a specific identifier
    return {"id": user_id, "name": "John Doe"}
"""
    with open("dummy.py", "w") as f:
        f.write(py_content)
        
    chunks = parse_file_to_chunks("dummy.py")
    
    # Simulate the ingestion loop
    collection = get_or_create_collection(repo_id)
    
    documents = [c.content for c in chunks]
    metadatas = [{"name": c.name, "type": c.chunk_type} for c in chunks]
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
    
    repos_dir = os.path.join(os.path.dirname(__file__), "data", "repos")
    os.makedirs(repos_dir, exist_ok=True)
    
    with open(os.path.join(repos_dir, f"{repo_id}_bm25.pkl"), "wb") as f:
        pickle.dump(bm25, f)
    with open(os.path.join(repos_dir, f"{repo_id}_chunks.pkl"), "wb") as f:
        pickle.dump(metadatas, f)
        
    os.remove("dummy.py")
    print(f"[SUCCESS] Ingestion complete for dummy repo. Extracted {len(chunks)} chunks.\n")

def test_queries(repo_id: str):
    # 1. Conceptual Query
    conceptual_query = "How does routing work?"
    print(f"--- Query: '{conceptual_query}' ---")
    results = retrieve_hybrid(repo_id, conceptual_query, top_k=2)
    for i, r in enumerate(results, 1):
        print(f"{i}. [RRF: {r.get('rrf_score', 0):.4f}] Name: {r['metadata']['name']}")
        
    print()
    
    # 2. Exact-Identifier Query
    exact_query = "fetchUserById"
    print(f"--- Query: '{exact_query}' ---")
    results = retrieve_hybrid(repo_id, exact_query, top_k=2)
    for i, r in enumerate(results, 1):
        print(f"{i}. [RRF: {r.get('rrf_score', 0):.4f}] Name: {r['metadata']['name']}")

if __name__ == "__main__":
    test_repo_id = "test-repo-stage3"
    setup_dummy_repo(test_repo_id)
    test_queries(test_repo_id)
