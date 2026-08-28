import sys
import os
import json
from dotenv import load_dotenv

load_dotenv()

from utils import get_gemini_client
from google import genai
from google.genai import types

def test_gemini():
    print("Testing Gemini Key Rotation with google.genai...")
    try:
        client = get_gemini_client()
        # Fallback to standard gemini-1.5-flash
        model_name = "gemini-3.1-flash-lite" 
        
        print(f"Using model: {model_name}")
        
        # Test basic generation
        response = client.models.generate_content(
            model=model_name,
            contents="Say hello!"
        )
        print(f"[SUCCESS] Basic response: {response.text.strip()}")
        
        # Test JSON mode
        json_resp = client.models.generate_content(
            model=model_name,
            contents="Output a JSON object with key 'status' and value 'ok'",
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        data = json.loads(json_resp.text)
        print(f"[SUCCESS] JSON response: {data}")
        
    except Exception as e:
        print(f"[ERROR] Failed to communicate with Gemini: {e}")

if __name__ == "__main__":
    test_gemini()
