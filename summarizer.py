import os
from dotenv import load_dotenv
import time
from utils import get_bedrock_client

load_dotenv()

FAST_MODEL_NAME = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

def generate_file_summary(file_path: str, file_content: str) -> str:
    """
    Generates a 1-sentence summary of the file's purpose to enrich chunk context.
    """
    try:
        client = get_bedrock_client()
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
        messages = [{"role": "user", "content": [{"text": prompt}]}]
        response = client.converse(
            modelId=FAST_MODEL_NAME,
            messages=messages
        )
        return response['output']['message']['content'][0]['text'].strip()
    except Exception as e:
        print(f"Warning: Failed to generate file summary for {file_path}: {e}")
        return ""
