import os
import json
import shutil
import boto3
from utils import clone_repo, get_files_to_index
from chunker import parse_file_to_chunks
from embeddings import get_embeddings_batch
from graph_builder import extract_and_store_graph, calculate_pagerank
import faiss
import numpy as np
import pickle

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "IngestionStatus")

def update_status(repo_id: str, status: str, error: str = None):
    try:
        table = dynamodb.Table(TABLE_NAME)
        table.update_item(
            Key={'repo_id': repo_id},
            UpdateExpression="SET #s = :status, #e = :error",
            ExpressionAttributeNames={'#s': 'status', '#e': 'error'},
            ExpressionAttributeValues={':status': status, ':error': error}
        )
    except Exception as e:
        print(f"Failed to update DynamoDB: {e}")

def upload_to_s3(local_path: str, s3_key: str):
    if not S3_BUCKET_NAME:
        print("WARNING: S3_BUCKET_NAME not set. Skipping upload.")
        return
    print(f"Uploading {local_path} to s3://{S3_BUCKET_NAME}/{s3_key}")
    s3.upload_file(local_path, S3_BUCKET_NAME, s3_key)

def lambda_handler(event, context):
    """
    Ingestion Worker Lambda:
    - Runs in the background (asynchronously invoked by Dispatcher).
    - Can run for up to 15 minutes.
    - Clones the repo to /tmp/, processes it, and uploads indices to S3.
    """
    repo_url = event.get('repo_url')
    repo_id = event.get('repo_id')
    
    if not repo_url or not repo_id:
        print("Error: Missing repo_url or repo_id in event payload.")
        return
        
    print(f"Starting background ingestion for {repo_id}")
    
    # Lambda provides 512MB to 10GB of ephemeral storage at /tmp
    tmp_dir = "/tmp"
    repo_dir = os.path.join(tmp_dir, "repos", repo_id)
    os.makedirs(os.path.join(tmp_dir, "repos"), exist_ok=True)
    
    try:
        update_status(repo_id, "cloning")
        
        # Stage 1: Clone
        success = clone_repo(repo_url, repo_dir)
        if not success:
            raise Exception("Failed to clone repository. Check URL and permissions.")
            
        update_status(repo_id, "indexing")
        
        # Stage 2: Chunking
        files = get_files_to_index(repo_dir)
        all_chunks = []
        for file_path in files:
            chunks = parse_file_to_chunks(file_path)
            if chunks:
                all_chunks.extend(chunks)
                
        if not all_chunks:
            raise Exception("No indexable code chunks found.")
            
        # Stage 3: Embedding & FAISS
        documents = []
        for chunk in all_chunks:
            doc = f"File: {chunk.name}\nType: {chunk.chunk_type}\n\n{chunk.content}"
            documents.append(doc)
            
        embeddings = get_embeddings_batch(documents, batch_size=5) # Throttle to respect Free Tier
        
        embeddings_np = np.array(embeddings).astype('float32')
        d = embeddings_np.shape[1]
        index = faiss.IndexFlatL2(d)
        index.add(embeddings_np)
        
        # Save FAISS
        faiss_path = os.path.join(tmp_dir, f"{repo_id}_faiss.bin")
        faiss.write_index(index, faiss_path)
        
        # Save Chunks
        chunks_path = os.path.join(tmp_dir, f"{repo_id}_chunks.pkl")
        with open(chunks_path, 'wb') as f:
            pickle.dump(all_chunks, f)
            
        # Stage 4: BM25
        from rank_bm25 import BM25Okapi
        tokenized_corpus = [doc.lower().split() for doc in documents]
        bm25 = BM25Okapi(tokenized_corpus)
        bm25_path = os.path.join(tmp_dir, f"{repo_id}_bm25.pkl")
        with open(bm25_path, 'wb') as f:
            pickle.dump(bm25, f)
            
        # Stage 5: Graph DB
        os.environ["DATA_DIR"] = tmp_dir
        graph_db_path = os.path.join(tmp_dir, f"{repo_id}_graph.db")
        extract_and_store_graph(repo_id, files)
        
        # Stage 6: Upload everything to S3
        upload_to_s3(faiss_path, f"{repo_id}/{repo_id}_faiss.bin")
        upload_to_s3(chunks_path, f"{repo_id}/{repo_id}_chunks.pkl")
        upload_to_s3(bm25_path, f"{repo_id}/{repo_id}_bm25.pkl")
        upload_to_s3(graph_db_path, f"{repo_id}/{repo_id}_graph.db")
        
        # Clean up /tmp to save ephemeral storage space for future warm invocations
        shutil.rmtree(repo_dir, ignore_errors=True)
        for f in [faiss_path, chunks_path, bm25_path, graph_db_path]:
            if os.path.exists(f):
                os.remove(f)
        
        # Complete
        update_status(repo_id, "completed")
        print(f"Ingestion perfectly complete for {repo_id}")
        
    except Exception as e:
        print(f"Worker Error: {e}")
        update_status(repo_id, "failed", str(e))
