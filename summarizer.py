import os
from dotenv import load_dotenv
import time
from utils import get_gemini_client

load_dotenv()

FAST_MODEL_NAME = "gemini-3.1-flash-lite"

def generate_file_summary(file_path: str, file_content: str) -> str:
    """
    Generates a 1-sentence summary of the file's purpose to enrich chunk context.
    """
    try:
        client = get_gemini_client()
    except Exception:
        return ""
        
    prompt = f"""
    You are an expert developer. Read the following code file and write a SINGLE SENTENCE 
    summarizing its primary purpose. Focus on what it does structurally or functionally.
    Do not use markdown, quotes, or conversational filler. 
    Just output the one sentence.
    
    File Path: {file_path}
    
    Code:
    {file_content[:8000]} # Truncate to save tokens, usually top imports/classes are enough
    """
    
    try:
        time.sleep(1)
        response = client.models.generate_content(
            model=FAST_MODEL_NAME,
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"Warning: Failed to generate file summary for {file_path}: {e}")
        return ""
