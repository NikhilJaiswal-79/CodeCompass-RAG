import os
import pickle
import numpy as np
import faiss
from embeddings import get_embedding

def retrieve_hybrid(repo_id: str, query: str, top_k: int = 10, mode: str = "hybrid"):
    """
    Performs retrieval. mode="hybrid" uses Vector Search + BM25 + RRF + CrossEncoder.
    mode="vector_only" uses only Vector Search (ChromaDB) for comparison.
    """
    # We fetch more than top_k for better fusion overlap and re-ranking
    fetch_k = 30
    
    # Load chunks metadata immediately as both vector and BM25 need it
    repos_dir = os.path.join(os.path.dirname(__file__), "data", "repos")
    chunks_path = os.path.join(repos_dir, f"{repo_id}_chunks.pkl")
    faiss_path = os.path.join(repos_dir, f"{repo_id}_faiss.bin")
    bm25_path = os.path.join(repos_dir, f"{repo_id}_bm25.pkl")
    
    chunk_metadatas = []
    if os.path.exists(chunks_path):
        with open(chunks_path, "rb") as f:
            chunk_metadatas = pickle.load(f)
            
    # 1. Vector Search (Dense / FAISS)
    vector_hits = []
    if os.path.exists(faiss_path) and chunk_metadatas:
        faiss_index = faiss.read_index(faiss_path)
        query_embedding = get_embedding(query)
        
        # FAISS expects a 2D numpy array
        query_np = np.array([query_embedding]).astype('float32')
        
        # search returns distances and indices
        distances, indices = faiss_index.search(query_np, fetch_k)
        
        if len(indices) > 0 and len(indices[0]) > 0:
            for i in range(len(indices[0])):
                idx = indices[0][i]
                if idx != -1 and idx < len(chunk_metadatas):  # Valid index
                    meta = chunk_metadatas[idx]
                    vector_hits.append({
                        "id": f"chunk_{idx}",
                        "content": meta.get("content", ""),
                        "metadata": meta,
                        "score": float(distances[0][i])
                    })
            
    if mode == "vector_only":
        return vector_hits[:top_k]
            
    # 2. Keyword Search (Sparse / BM25)
    bm25_hits = []
    
    if os.path.exists(bm25_path) and chunk_metadatas:
        from utils import tokenize_for_bm25
        with open(bm25_path, "rb") as f:
            bm25 = pickle.load(f)
        tokenized_query = tokenize_for_bm25(query)
        base_doc_scores = bm25.get_scores(tokenized_query)
        
        # Fetch PageRank scores from SQLite
        from graph_db import get_graph_db_connection
        pagerank_map = {}
        try:
            conn = get_graph_db_connection(repo_id)
            cursor = conn.cursor()
            cursor.execute("SELECT name, pagerank_score FROM nodes")
            for name, score in cursor.fetchall():
                if score is not None:
                    if name not in pagerank_map or score > pagerank_map[name]:
                        pagerank_map[name] = score
            conn.close()
        except Exception as e:
            print(f"Failed to load PageRank scores: {e}")
            
        # Boost BM25 scores with PageRank (Tri-Modal)
        doc_scores = []
        for idx, score in enumerate(base_doc_scores):
            meta = chunk_metadatas[idx]
            name = meta.get("name")
            pr_score = pagerank_map.get(name, 0.15) if name else 0.15
            # Boost keyword score by graph centrality (e.g. 5x multiplier for high PR)
            boosted_score = score * (1.0 + (pr_score * 5.0))
            doc_scores.append(boosted_score)
        
        scored_docs = sorted(enumerate(doc_scores), key=lambda x: x[1], reverse=True)
        
        top_bm25_ids = []
        top_bm25_metas = []
        top_bm25_scores = []
        for idx, score in scored_docs[:fetch_k]:
            if score > 0:
                top_bm25_ids.append(f"chunk_{idx}")
                top_bm25_metas.append(chunk_metadatas[idx])
                top_bm25_scores.append(score)
                
        if top_bm25_ids:
            for i, doc_id in enumerate(top_bm25_ids):
                meta = top_bm25_metas[i]
                bm25_hits.append({
                    "id": doc_id,
                    "content": meta.get("content", ""),
                    "metadata": meta,
                    "score": top_bm25_scores[i]
                })
    # 3. Reciprocal Rank Fusion (RRF)
    RRF_K = 60
    fused_scores = {}
    fused_docs = {}
    
    for rank, hit in enumerate(vector_hits, 1):
        doc_id = hit["id"]
        fused_scores[doc_id] = fused_scores.get(doc_id, 0) + (1.0 / (RRF_K + rank))
        fused_docs[doc_id] = hit
        
    for rank, hit in enumerate(bm25_hits, 1):
        doc_id = hit["id"]
        # BM25 gets 2x weight vs vector — exact keyword matching is more
        # reliable than embeddings for code identifiers like function names.
        fused_scores[doc_id] = fused_scores.get(doc_id, 0) + (2.0 / (RRF_K + rank))
        if doc_id not in fused_docs:
            fused_docs[doc_id] = hit
            
    sorted_fused_docs = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
    
    # 4. Return candidates sorted by BM25-weighted RRF score.
    # We intentionally skip cross-encoder reranking here because
    # ms-marco cross-encoders are trained on web text and actively
    # hurt code retrieval by demoting TypeScript/JavaScript chunks
    # that use camelCase identifiers and dense syntax.
    candidates = []
    for doc_id, score in sorted_fused_docs[:top_k]:
        hit = fused_docs[doc_id]
        hit["rrf_score"] = score
        candidates.append(hit)
    
    return candidates

