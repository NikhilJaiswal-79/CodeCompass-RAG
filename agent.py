import os
import json
from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
from retrieval import retrieve_hybrid
from graph_queries import get_callers, get_callees
from utils import get_gemini_client
from google.genai import types
import time

def generate_with_retry(client, model, contents, config=None):
    for i in range(5):
        try:
            return client.models.generate_content(model=model, contents=contents, config=config)
        except Exception as e:
            if i == 4: raise e
            print(f"Gemini API limit/error hit. Fetching new key and retrying in 5s... ({e})")
            time.sleep(5)
            # Fetch a new random client to rotate the API key
            from utils import get_gemini_client
            client = get_gemini_client()

load_dotenv()

class AgentState(TypedDict):
    repo_id: str
    query: str
    sub_queries: list[str]
    graph_targets: list[str]
    hypothetical_code: str
    context_chunks: Annotated[list[dict], operator.add]
    graph_context: Annotated[list[str], operator.add]
    rules: dict
    iterations: int
    final_answer: str
    next_action: str
    retrieval_mode: str

MODEL_NAME = "gemini-3.1-flash-lite"
FAST_MODEL = "gemini-3.1-flash-lite"

def plan_queries(state: AgentState):
    print("--- [Agent] Planning Queries ---")
    try:
        client = get_gemini_client()
    except Exception:
        return {"sub_queries": [state["query"]], "graph_targets": [], "hypothetical_code": ""}
    
    prompt = f"""
    You are an expert developer searching a codebase. 
    The user asked: "{state['query']}"
    
    Break this down into targeted search strategies.
    1. search_queries: 1-3 strings for hybrid vector/keyword search.
    2. hypothetical_code: If it's a conceptual question, write a 3-5 line fake python/js code snippet of what the solution might look like (HyDE). If not, leave empty.
    3. graph_targets: If the user mentions a specific function/class name (e.g. "initialize_database"), list it here to query the dependency graph for callers/callees.
    
    Output ONLY a JSON object in this exact format:
    {{
      "search_queries": ["query 1", "query 2"],
      "hypothetical_code": "def fake_func(): pass",
      "graph_targets": ["specific_function_name"]
    }}
    """
    
    try:
        response = generate_with_retry(
            client=client,
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        data = json.loads(response.text)
    except Exception as e:
        print(f"Error calling Gemini in plan_queries: {e}")
        return {"sub_queries": [state["query"]], "graph_targets": [], "hypothetical_code": ""}
    
    # Merge seeded targets with newly extracted ones
    existing_targets = state.get("graph_targets", [])
    new_targets = data.get("graph_targets", [])
    combined_targets = list(set(existing_targets + new_targets))
    
    return {
        "sub_queries": data.get("search_queries", [state["query"]]),
        "hypothetical_code": data.get("hypothetical_code", ""),
        "graph_targets": combined_targets
    }

def execute_search(state: AgentState):
    print("--- [Agent] Executing Search ---")
    repo_id = state["repo_id"]
    new_chunks = []
    
    queries = list(state.get("sub_queries", []))
    if state.get("hypothetical_code"):
        queries.append(state["hypothetical_code"])
    
    # CRITICAL: Also search using exact function/class names from graph_targets.
    # BM25 can match identifiers like "createCorsair" or "processWebhook" exactly,
    # which is far more precise than semantic embedding search for code.
    for target in state.get("graph_targets", []):
        if target and target.strip() and target not in queries:
            queries.append(target.strip())
        
    mode = state.get("retrieval_mode", "hybrid")
        
    for q in queries:
        if not q.strip(): continue
        results = retrieve_hybrid(repo_id, q, top_k=8, mode=mode)
        for r in results:
            existing_ids = [c["id"] for c in state.get("context_chunks", [])] + [c["id"] for c in new_chunks]
            if r["id"] not in existing_ids:
                new_chunks.append(r)

                
    new_graph_context = []
    for target in state.get("graph_targets", []):
        if not target.strip(): continue
        try:
            callers = get_callers(repo_id, target)
            callees = get_callees(repo_id, target)
            if callers or callees:
                graph_info = f"Dependency Graph for '{target}':\n"
                if callers:
                    graph_info += f"  - Called by: {', '.join([c['caller_name'] for c in callers])}\n"
                if callees:
                    graph_info += f"  - Calls: {', '.join([c['callee_name'] for c in callees])}\n"
                new_graph_context.append(graph_info)
        except Exception:
            pass
                
    rules = state.get("rules", {})
    if not rules:
        repos_dir = os.path.join(os.path.dirname(__file__), "data", "repos")
        rules_path = os.path.join(repos_dir, f"{repo_id}_rules.json")
        if os.path.exists(rules_path):
            with open(rules_path, "r") as f:
                rules = json.load(f)
                
    return {
        "context_chunks": new_chunks,
        "graph_context": new_graph_context,
        "rules": rules,
        "iterations": state.get("iterations", 0) + 1
    }

def compress_context(state: AgentState):
    print("--- [Agent] Compressing Context ---")
    try:
        client = get_gemini_client()
    except Exception:
        return {}
    
    for c in state.get("context_chunks", []):
        content = c.get("content", "")
        if len(content) > 1500:
            prompt = f"Extract ONLY the lines of code relevant to this query: '{state['query']}'. Do not add markdown blocks, conversational text, or explanations. If the whole chunk is relevant, return it.\n\nCode:\n{content[:6000]}"
            try:
                response = generate_with_retry(
                    client=client,
                    model=FAST_MODEL,
                    contents=prompt
                )
                c["content"] = response.text.strip()
            except Exception:
                pass
    return {} 

def generate_or_replan(state: AgentState):
    print("--- [Agent] Reviewing Context & Generating ---")
    try:
        client = get_gemini_client()
    except Exception:
        return {"next_action": "end", "final_answer": "Error initializing Gemini."}
    
    context_str = ""
    for c in state.get("context_chunks", []):
        file_path = c.get("metadata", {}).get("file_path", "unknown")
        name = c.get("metadata", {}).get("name", "unknown")
        content = c.get("content", "")
        # Sanitize: lone backslashes in TypeScript code (regex, string escapes)
        # break json.loads when Gemini wraps context in a JSON response.
        safe_content = content.replace("\\", "/")
        context_str += f"\n\n--- FILE: {file_path} | NAME: {name} ---\n{safe_content}"
        
    for gc in state.get("graph_context", []):
        context_str += f"\n\n--- GRAPH DATA ---\n{gc}"
        
    rules_str = json.dumps(state.get("rules", {}), indent=2)
    
    prompt = f"""
    You are an expert codebase assistant. The user asked: "{state['query']}"
    
    Here is the retrieved code and graph context:
    {context_str}
    
    Here are the repository contribution rules you MUST enforce if providing code:
    {rules_str}
    
    CRITICAL INSTRUCTIONS:
    1. You MUST NOT hallucinate. Do not mention any files, functions, or concepts that are not explicitly present in the provided context.
    2. If the context does not contain the answer, or if the feature does not exist in the codebase, you MUST state "The provided context does not contain the answer" or "This feature does not exist in the codebase" and stop.
    3. Be EXHAUSTIVELY SPECIFIC in your answer:
       - Name exact function names, variable names, parameter names, and type names from the code.
       - Describe the exact sequence of operations (e.g. "first calls X, then checks Y, then returns Z").
       - Quote or paraphrase specific code logic, not vague summaries.
       - If the code does conditional branching, describe each branch.
    4. If the question asks about something that does NOT exist in the codebase, clearly state it does not exist and explain what actually exists instead.
    5. Your answer must directly address every part of a multi-part question.
    
    Task: Review the code context. 
    If the context contains enough information to accurately answer the user's question, output a final markdown answer.
    If the context is entirely missing the required files or logic, you may request a new search by providing a new search query.
    
    Output ONLY a JSON object in this exact format:
    {{
       "action": "answer",
       "text": "Your detailed markdown answer here, citing the files used."
    }}
    OR
    {{
       "action": "search",
       "new_queries": ["a highly specific keyword query to find the missing code"]
    }}
    """
    
    try:
        response = generate_with_retry(
            client=client,
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        data = json.loads(response.text)
    except Exception as e:
        print(f"Error in generate_or_replan: {e}")
        return {"next_action": "end", "final_answer": "Error generating response."}
        
    action = data.get("action", "answer")
    iterations = state.get("iterations", 0)
    
    if action == "search" and iterations < 2:
        return {
            "sub_queries": data.get("new_queries", [state["query"]]),
            "next_action": "search"
        }
    else:
        return {
            "final_answer": data.get("text", "Could not generate an answer based on the provided context."),
            "next_action": "end"
        }

def route_next_step(state: AgentState):
    if state["next_action"] == "search":
        return "execute_search"
    return END

def build_agent_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("plan_queries", plan_queries)
    workflow.add_node("execute_search", execute_search)
    workflow.add_node("generate_or_replan", generate_or_replan)
    
    workflow.set_entry_point("plan_queries")
    workflow.add_edge("plan_queries", "execute_search")
    workflow.add_edge("execute_search", "generate_or_replan")
    
    workflow.add_conditional_edges(
        "generate_or_replan",
        route_next_step,
        {
            "execute_search": "execute_search",
            END: END
        }
    )
    
    return workflow.compile()
