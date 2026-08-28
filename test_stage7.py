import os
import shutil
import pickle
from chunker import Chunk
from database import get_or_create_collection
from embeddings import get_embedding
from rank_bm25 import BM25Okapi
from retrieval import retrieve_hybrid

def setup_dummy_repo_for_rerank(repo_id: str):
    repos_dir = os.path.join(os.path.dirname(__file__), "data", "repos")
    os.makedirs(repos_dir, exist_ok=True)
    
    # Create ambiguous chunks
    chunks = [
        Chunk(file_path="auth_v1.py", content="def authenticate():\n    # LEGACY: Do not use for new database connections\n    pass", name="authenticate", chunk_type="function", start_line=1, end_line=3, language="python"),
        Chunk(file_path="db_utils.py", content="def connect_db():\n    # Connects to the database, but does not handle auth\n    pass", name="connect_db", chunk_type="function", start_line=1, end_line=3, language="python"),
        Chunk(file_path="auth_v2.py", content="def authenticate_db_connection(token):\n    # MODERN: Use this to securely authenticate to the primary database\n    pass", name="authenticate_db_connection", chunk_type="function", start_line=1, end_line=3, language="python"),
        Chunk(file_path="random.py", content="def random_auth_stuff():\n    # Just some random text about authentication that might trigger BM25 database database\n    pass", name="random_auth_stuff", chunk_type="function", start_line=1, end_line=3, language="python"),
    ]
    
    collection = get_or_create_collection(repo_id)
    documents = [c.content for c in chunks]
    metadatas = [{"name": c.name, "type": c.chunk_type, "file_path": c.file_path} for c in chunks]
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    embeddings = [get_embedding(doc) for doc in documents]
    
    collection.add(documents=documents, embeddings=embeddings, metadatas=metadatas, ids=ids)
    
    tokenized = [doc.lower().split() for doc in documents]
    bm25 = BM25Okapi(tokenized)
    
    with open(os.path.join(repos_dir, f"{repo_id}_bm25.pkl"), "wb") as f:
        pickle.dump(bm25, f)
    with open(os.path.join(repos_dir, f"{repo_id}_chunks.pkl"), "wb") as f:
        pickle.dump(metadatas, f)

def run_test():
    test_repo_id = "test-rerank-repo"
    print("--- Setting up dummy repo ---")
    setup_dummy_repo_for_rerank(test_repo_id)
    
    query = "How to securely authenticate to the primary database?"
    print(f"\n--- Query: '{query}' ---")
    
    print("\n--- Results (with CrossEncoder Re-ranking) ---")
    # Top 3
    results = retrieve_hybrid(test_repo_id, query, top_k=3)
    
    for i, res in enumerate(results):
        print(f"\n#{i+1}: {res['metadata']['name']} (RRF: {res.get('rrf_score', 0):.4f} | CrossEncoder: {res.get('cross_score', 0):.4f})")
        print(f"Content: {res['content'].strip()}")
        
if __name__ == "__main__":
    run_test()
