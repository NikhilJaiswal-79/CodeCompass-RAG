import os
import json
from dotenv import load_dotenv
from utils import get_gemini_client
from google.genai import types

load_dotenv()

MODEL_NAME = "gemini-3.1-flash-lite"

def find_guideline_files(repo_path: str) -> list[str]:
    candidates = [
        "CONTRIBUTING.md",
        "README.md",
        ".github/CONTRIBUTING.md",
        "docs/CONTRIBUTING.md"
    ]
    
    found_files = []
    for candidate in candidates:
        full_path = os.path.join(repo_path, candidate)
        if os.path.exists(full_path):
            found_files.append(full_path)
            
    return found_files

def extract_rules(markdown_text: str) -> dict:
    try:
        client = get_gemini_client()
    except Exception:
        print("Warning: GEMINI_API_KEY not found. Skipping rule extraction.")
        return {"rules": []}
    
    prompt = """
    You are an expert developer analyzing a repository's contribution guidelines or README.
    Extract the core rules, coding standards, formatting requirements, testing requirements, 
    and architectural invariants that a contributor MUST follow.
    
    Respond ONLY with a JSON object in this exact format, with no markdown formatting or extra text:
    {
      "coding_standards": ["rule 1", "rule 2"],
      "testing_requirements": ["rule 1"],
      "process_rules": ["rule 1"]
    }
    
    If a category has no rules mentioned, leave the array empty.
    Keep the rules concise and actionable.
    """
    
    try:
        max_chars = 15000
        truncated_text = markdown_text[:max_chars]
        
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=f"{prompt}\n\nTEXT:\n{truncated_text}",
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        
        response_text = response.text
        return json.loads(response_text)
    except Exception as e:
        print(f"Failed to extract rules via Gemini: {e}")
        return {"coding_standards": [], "testing_requirements": [], "process_rules": []}

def process_guidelines(repo_id: str, repo_path: str):
    print(f"[{repo_id}] Scanning for contribution guidelines...")
    guideline_files = find_guideline_files(repo_path)
    
    if not guideline_files:
        print(f"[{repo_id}] No standard guideline files found.")
        return
        
    all_text = ""
    for file_path in guideline_files:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                all_text += f"\n\n--- Contents of {os.path.basename(file_path)} ---\n"
                all_text += f.read()
        except Exception as e:
            print(f"Failed to read {file_path}: {e}")
            
    if not all_text.strip():
        return
        
    print(f"[{repo_id}] Extracting rules using Gemini ({MODEL_NAME})...")
    extracted_rules = extract_rules(all_text)
    
    repos_dir = os.path.join(os.path.dirname(__file__), "data", "repos")
    os.makedirs(repos_dir, exist_ok=True)
    
    rules_path = os.path.join(repos_dir, f"{repo_id}_rules.json")
    with open(rules_path, "w", encoding="utf-8") as f:
        json.dump(extracted_rules, f, indent=2)
        
    print(f"[{repo_id}] Successfully extracted and saved repository rules.")
