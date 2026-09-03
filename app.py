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
    
    # Bug Fix: Check if the final FAISS index actually exists, not just the cloned folder!
    faiss_path = f"{repo_path}_faiss.bin"
    if os.path.exists(faiss_path):
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

custom_css = """
body, html {
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%) !important;
    color: #e2e8f0;
    height: 100vh !important;
    margin: 0 !important;
    overflow: hidden !important;
}
.gradio-container {
    background: transparent !important;
    border: none !important;
    height: 100vh !important;
    max-width: 100% !important;
    padding: 10px 20px !important;
    display: flex !important;
    flex-direction: column !important;
}
/* Allow only the chat area to scroll, not the whole page */
.gr-box, .gr-panel, .gr-form {
    background: rgba(30, 41, 59, 0.6) !important;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 16px !important;
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5) !important;
}
/* Ensure the chatbot expands to fill the space */
.wrap.svelte-1bup4q2 {
    flex-grow: 1 !important;
    overflow: hidden !important;
}
/* Premium Button */
button.primary {
    background: linear-gradient(90deg, #6366f1 0%, #a855f7 100%) !important;
    border: none !important;
    color: white !important;
    font-weight: 700 !important;
    border-radius: 12px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4) !important;
}
button.primary:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(99, 102, 241, 0.6) !important;
}
/* Gradient Text for Main Title */
h1 {
    background: -webkit-linear-gradient(45deg, #818cf8, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 900 !important;
    letter-spacing: -0.5px;
    margin: 0 !important;
    padding-bottom: 5px !important;
}
/* Hide Gradio Footer Buttons */
footer {
    display: none !important;
}
"""

# Build the Custom UI Layout
with gr.Blocks(title="Universal GitHub Architecture Assistant", css=custom_css, fill_height=True) as demo:
    gr.Markdown(
        """
        # 🚀 CodeCompass Architecture Assistant
        Ask complex architectural questions about **ANY** GitHub codebase. The agent uses Tri-Modal Hybrid Retrieval (BM25 + Vector + Graph PageRank) to find the exact code chunks you need.
        """
    )
    
    with gr.Row():
        # Left Sidebar (25% of screen) for Ingestion
        with gr.Column(scale=1):
            gr.Markdown("### 🛠️ Repository Ingestion")
            repo_input = gr.Textbox(
                label="GitHub Repo URL", 
                placeholder="https://github.com/username/repository",
                info="Paste any public GitHub repository URL here to dynamically ingest and chat with it!"
            )
            ingest_btn = gr.Button("Ingest Repository", variant="primary", size="lg")
            ingestion_status = gr.Textbox(label="Ingestion Progress", interactive=False, lines=6)
            
        # Right Main Area (75% of screen) for Chatbot
        with gr.Column(scale=3):
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
    demo.launch(server_name="0.0.0.0", server_port=7860)
