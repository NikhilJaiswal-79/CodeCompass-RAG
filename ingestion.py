import os

from utils import clone_repo, get_files_to_index

# In-memory status store for simplicity in Stage 1
# Format: { "repo_id": {"status": "pending|cloning|indexing|completed|failed", "error": ""} }
indexing_status = {}

def process_repo(repo_url: str, repo_id: str):
    """
    Background task logic to ingest a repository. Now yields progress updates.
    """
    try:
        indexing_status[repo_id] = {"status": "cloning", "error": None}
        
        # Target directory for the cloned repo
        repos_dir = os.path.join(os.path.dirname(__file__), "data", "repos")
        os.makedirs(repos_dir, exist_ok=True)
        target_dir = os.path.join(repos_dir, repo_id)
        
        yield f"⏳ **Stage 1/5**: Cloning repository {repo_url}..."
        print(f"[{repo_id}] Starting clone for {repo_url}...")
        success = clone_repo(repo_url, target_dir)
        
        if not success:
            indexing_status[repo_id] = {"status": "failed", "error": "Failed to clone repository."}
            yield "❌ **Error**: Failed to clone repository."
            return
            
        indexing_status[repo_id] = {"status": "indexing", "error": None}
        yield "⏳ **Stage 2/5**: Discovering files and preparing chunker..."
        
        # Discover files
        files = get_files_to_index(target_dir)
        yield f"⏳ **Stage 2/5**: Discovered {len(files)} files. Chunking..."
        
        
        # Stage 2: Chunking (Context Enrichment disabled for speed/rate-limits)
        from chunker import parse_file_to_chunks
        
        all_chunks = []
        for file_path in files:
            chunks = parse_file_to_chunks(file_path)
            if chunks:
                all_chunks.extend(chunks)
            
        if not all_chunks:
            yield "✅ **Complete**: No code chunks found to index."
            indexing_status[repo_id] = {"status": "completed", "error": None, "files_discovered": len(files), "chunks_extracted": 0}
            return
            
        yield f"⏳ **Stage 3/5**: Generating embeddings for {len(all_chunks)} chunks and saving to FAISS..."
        
        # Stage 3: Embedding & BM25 Storage
        from embeddings import get_embedding
        import pickle
        import numpy as np
        import faiss
        from rank_bm25 import BM25Okapi
        
        # Prepare data for FAISS and Metadata
        documents = [chunk.content for chunk in all_chunks]
        metadatas = [{
            "content": chunk.content,  # FAISS doesn't store text, so we save it here
            "file_path": chunk.file_path, 
            "start_line": chunk.start_line, 
            "end_line": chunk.end_line,
            "name": chunk.name,
            "chunk_type": chunk.chunk_type,
            "language": chunk.language
        } for chunk in all_chunks]
        
        # Generate embeddings in batches to prevent 429 Rate Limits
        from embeddings import get_embeddings_batch
        embeddings = get_embeddings_batch(documents, batch_size=100)
        
        # Add to FAISS Index
        embeddings_np = np.array(embeddings).astype('float32')
        d = embeddings_np.shape[1] # Dimension (768 for Gemini)
        index = faiss.IndexFlatL2(d)
        index.add(embeddings_np)
        
        # Save FAISS index to disk
        faiss_path = os.path.join(repos_dir, f"{repo_id}_faiss.bin")
        faiss.write_index(index, faiss_path)
        
        yield "⏳ **Stage 3/5**: Building BM25 exact-match keyword index..."
        from utils import tokenize_for_bm25
        
        tokenized_corpus = [tokenize_for_bm25(doc) for doc in documents]
        bm25 = BM25Okapi(tokenized_corpus)
        
        # Save BM25 index to disk
        bm25_path = os.path.join(repos_dir, f"{repo_id}_bm25.pkl")
        with open(bm25_path, "wb") as f:
            pickle.dump(bm25, f)
            
        # Also save the raw chunks so retrieval can map index -> chunk metadata easily
        chunks_path = os.path.join(repos_dir, f"{repo_id}_chunks.pkl")
        with open(chunks_path, "wb") as f:
            # We can just dump the dicts
            pickle.dump(metadatas, f)
            
        yield "⏳ **Stage 4/5**: Building code dependency graph..."
        # Stage 4: Dependency Graph
        from graph_builder import extract_and_store_graph
        extract_and_store_graph(repo_id, files)
        
        yield "⏳ **Stage 5/5**: Processing contribution guidelines..."
        # Stage 5: Contribution Guidelines
        from guidelines import process_guidelines
        process_guidelines(repo_id, target_dir)
        
        indexing_status[repo_id] = {
            "status": "completed", 
            "error": None, 
            "files_discovered": len(files),
            "chunks_extracted": len(all_chunks)
        }
        yield "✅ **Ingestion Complete!** The repository is fully indexed and ready for chatting."
    except Exception as e:
        import traceback
        traceback.print_exc()
        indexing_status[repo_id] = {"status": "failed", "error": str(e)}
        yield f"❌ **Error during ingestion**: {e}"
