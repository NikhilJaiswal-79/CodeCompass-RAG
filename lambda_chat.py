import json
import os
import boto3
from agent import build_agent_graph

s3 = boto3.client('s3')
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")

# Build the LangGraph agent globally so it stays warm across invocations
graph = build_agent_graph()

def ensure_artifacts_downloaded(repo_id: str):
    """
    Checks if the artifacts are already cached in Lambda's /tmp.
    If not, downloads them from S3.
    """
    tmp_dir = "/tmp"
    artifacts = [
        f"{repo_id}_faiss.bin",
        f"{repo_id}_chunks.pkl",
        f"{repo_id}_bm25.pkl",
        f"{repo_id}_graph.db",
        f"{repo_id}_rules.json" # Might not exist yet if rules step failed, but we try
    ]
    
    for artifact in artifacts:
        local_path = os.path.join(tmp_dir, artifact)
        s3_key = f"{repo_id}/{artifact}"
        if not os.path.exists(local_path):
            try:
                print(f"Downloading {artifact} from S3...")
                s3.download_file(S3_BUCKET_NAME, s3_key, local_path)
            except Exception as e:
                print(f"Warning: Could not download {artifact}. It might not exist. Error: {e}")

def lambda_handler(event, context):
    """
    Chat Lambda:
    - Receives HTTP API Gateway requests (POST /chat).
    - Downloads S3 artifacts to /tmp if not already there (Warm Start).
    - Runs the LangGraph AI agent.
    - Returns the final Markdown response.
    """
    os.environ["DATA_DIR"] = "/tmp"
    try:
        body = json.loads(event.get('body', '{}'))
        repo_url = body.get('repo_url')
        message = body.get('message')
        history = body.get('history', [])
        
        if not repo_url or not message:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing 'repo_url' or 'message'."})
            }
            
        repo_id = repo_url.rstrip("/").split("/")[-2] + "-" + repo_url.rstrip("/").split("/")[-1]
        
        # 1. Download artifacts from S3 to /tmp
        ensure_artifacts_downloaded(repo_id)
        
        # 2. Format history
        context_str = ""
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            context_str += f"{role.capitalize()}: {content}\n"
            
        # 3. Build input state for LangGraph
        initial_state = {
            "query": message,
            "repo_id": repo_id,
            "sub_queries": [],
            "graph_targets": [],
            "hypothetical_code": "",
            "context_chunks": [],
            "graph_context": [],
            "rules": {},
            "iterations": 0,
            "final_answer": "",
            "next_action": "",
            "retrieval_mode": "hybrid"
        }
        
        # 4. Execute the Graph synchronously
        final_state = None
        for output in graph.stream(initial_state, {"recursion_limit": 25}):
            for key, value in output.items():
                final_state = value
                
        # 5. Extract the final answer
        if final_state and final_state.get("final_answer"):
            answer = final_state["final_answer"]
        else:
            answer = "Could not generate an answer based on the provided context."
            
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"response": answer})
        }
        
    except Exception as e:
        print(f"Chat Error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
