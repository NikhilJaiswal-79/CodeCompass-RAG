import os
import gradio as gr
from agent import build_agent_graph
from ingestion import process_repo

# Initialize your LangGraph agent globally so it's ready when the server starts
print("Building Agent Graph...")
graph = build_agent_graph()

def extract_repo_id(url: str) -> str:
    url = url.strip().rstrip("/")
    if "github.com/" in url:
        parts = url.split("github.com/")[-1].split("/")
    else:
        parts = url.split("/")
    if len(parts) >= 2:
        return f"{parts[-2]}-{parts[-1]}"
    return "unknown-repo"

def ingest_handler(repo_url):
    repo_id = extract_repo_id(repo_url)
    repo_path = os.path.join(os.path.dirname(__file__), "data", "repos", repo_id)
    if os.path.exists(repo_path):
        yield "✅ Repository already ingested! You can start chatting."
        return
        
    for progress_message in process_repo(repo_url, repo_id):
        yield progress_message

def chat_with_agent(message, history, repo_url):
    """
    This function processes the incoming chat message and history, 
    routes it through the LangGraph RAG agent, and returns the markdown response.
    """
    repo_id = extract_repo_id(repo_url)
    repo_path = os.path.join(os.path.dirname(__file__), "data", "repos", repo_id)
    
    from ingestion import indexing_status
    status_info = indexing_status.get(repo_id)
    
    # Check if ingestion is currently running or hasn't started
    if status_info and status_info.get("status") not in ["completed", "failed"]:
        yield "⏳ **Please wait!** The repository is currently being ingested. You cannot ask questions until it finishes."
        return
    elif not os.path.exists(repo_path):
        yield "❌ **Error**: You must click 'Ingest Repository' before asking a question!"
        return
        
    yield "🔍 Searching the codebase..."
    
    # 2. Format the conversation history into the query if there are follow-up questions
    context = ""
    if history:
        # Gradio 6 passes history as a list of dicts: [{"role": "user", "content": "..."}, ...]
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                context += f"User: {content}\n"
            else:
                context += f"Agent: {content}\n\n"
                
    full_query = message
    if context:
        full_query = f"Previous Conversation Context:\n{context}Current Question: {message}"

    # 3. Setup the initial LangGraph Agent State
    state = {
        "repo_id": repo_id,
        "query": full_query,
        "sub_queries": [],
        "graph_targets": [],
        "hypothetical_code": "",
        "context_chunks": [],
        "graph_context": [],
        "rules": {},
        "iterations": 0,
        "final_answer": "",
        "next_action": "",
        "retrieval_mode": "hybrid" # Force hybrid tri-modal retrieval
    }
    
    # 4. Invoke the graph
    print(f"Incoming Query: {message} for Repo: {repo_id}")
    final_state = graph.invoke(state)
    
    # 5. Return the generated answer
    yield final_state.get("final_answer", "Error: The agent could not generate an answer.")

# Build the Custom UI Layout
with gr.Blocks(title="Universal GitHub Architecture Assistant", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 🚀 Universal GitHub Architecture Assistant
        Ask complex architectural questions about **ANY** GitHub codebase. The agent uses Tri-Modal Hybrid Retrieval (BM25 + Vector + Graph PageRank) to find the exact code chunks you need.
        """
    )
    
    with gr.Row():
        # Left Sidebar (20% of screen) for Ingestion
        with gr.Column(scale=1):
            gr.Markdown("### 🛠️ Repository Ingestion")
            repo_input = gr.Textbox(
                label="GitHub Repo URL", 
                value="https://github.com/corsairdev/corsair", 
                info="Paste any public GitHub repository URL here to dynamically ingest and chat with it!"
            )
            ingest_btn = gr.Button("Ingest Repository", variant="primary")
            ingestion_status = gr.Textbox(label="Ingestion Progress", interactive=False, lines=6)
            
        # Right Main Area (80% of screen) for Chatbot
        with gr.Column(scale=4):
            chat_interface = gr.ChatInterface(
                fn=chat_with_agent,
                additional_inputs=[repo_input]
            )
    
    # Wire the ingest button to the ingest handler
    ingest_btn.click(
        fn=ingest_handler,
        inputs=[repo_input],
        outputs=[ingestion_status]
    )

if __name__ == "__main__":
    # Launching on 0.0.0.0 is required for Hugging Face Spaces!
    demo.launch(server_name="0.0.0.0", server_port=7860)
