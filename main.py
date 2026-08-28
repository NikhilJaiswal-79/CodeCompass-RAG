from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import uuid
import os

from ingestion import process_repo, indexing_status
from agent import build_agent_graph
import json
from fastapi.responses import StreamingResponse

load_dotenv()

app = FastAPI(title="ContribLens")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for local testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class IndexRequest(BaseModel):
    url: str

class ChatRequest(BaseModel):
    query: str

@app.get("/")
def read_root():
    return {"message": "Welcome to ContribLens API"}

@app.post("/index-repo", status_code=202)
def index_repo(request: IndexRequest, background_tasks: BackgroundTasks):
    """
    Accepts a repository URL, generates a unique repo_id, and enqueues it for indexing.
    """
    if not request.url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL format. Must start with http/https.")
        
    parts = request.url.rstrip("/").split("/")
    if len(parts) >= 2:
        base_id = f"{parts[-2]}-{parts[-1]}".replace(".git", "")
    else:
        base_id = "repo"
        
    repo_id = f"{base_id}-{str(uuid.uuid4())[:8]}"
    indexing_status[repo_id] = {"status": "pending", "error": None}
    
    background_tasks.add_task(process_repo, request.url, repo_id)
    
    return {"message": "Indexing started", "repo_id": repo_id}

@app.get("/index-status/{repo_id}")
def get_index_status(repo_id: str):
    """
    Returns the current status of the indexing process for a given repo_id.
    """
    status_info = indexing_status.get(repo_id)
    if not status_info:
        raise HTTPException(status_code=404, detail="Repository ID not found.")
        
    return status_info

@app.post("/chat/{repo_id}")
def chat_with_agent(repo_id: str, request: ChatRequest):
    """
    Invokes the LangGraph Agentic RAG pipeline for the given repository.
    """
    repos_dir = os.path.join(os.path.dirname(__file__), "data", "repos")
    if not os.path.exists(os.path.join(repos_dir, repo_id)):
        raise HTTPException(status_code=404, detail="Repository not indexed yet.")
        
    graph = build_agent_graph()
    
    initial_state = {
        "repo_id": repo_id,
        "query": request.query,
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
    
    try:
        final_state = graph.invoke(initial_state)
        return {"answer": final_state["final_answer"]}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/stream/{repo_id}")
def chat_stream_with_agent(repo_id: str, request: ChatRequest):
    """
    Invokes the LangGraph Agentic RAG pipeline and streams internal states (SSE).
    """
    repos_dir = os.path.join(os.path.dirname(__file__), "data", "repos")
    if not os.path.exists(os.path.join(repos_dir, repo_id)):
        raise HTTPException(status_code=404, detail="Repository not indexed yet.")
        
    graph = build_agent_graph()
    
    initial_state = {
        "repo_id": repo_id,
        "query": request.query,
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
    
    def event_stream():
        try:
            for event in graph.stream(initial_state):
                for node_name, state_update in event.items():
                    # Stream the node name to the frontend
                    yield f"data: {json.dumps({'node': node_name})}\n\n"
                    
                    if state_update and isinstance(state_update, dict) and "final_answer" in state_update and state_update["final_answer"]:
                        # When it reaches the end, stream the final answer
                        yield f"data: {json.dumps({'answer': state_update['final_answer']})}\n\n"
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
    return StreamingResponse(event_stream(), media_type="text/event-stream")
