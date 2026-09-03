import os
from dotenv import load_dotenv
from google import genai

# Load .env variables into os.environ
load_dotenv()

_clients = []
_current_client_idx = 0

def _get_clients():
    global _clients
    if not _clients:
        keys = [
            os.environ.get("GEMINI_API_KEY_1"),
            os.environ.get("GEMINI_API_KEY_2"),
            os.environ.get("GEMINI_API_KEY_3")
        ]
        # Filter out empty/None keys
        keys = [k for k in keys if k]
        # If no keys, fallback to standard GEMINI_API_KEY
        if not keys:
            keys = [os.environ.get("GEMINI_API_KEY")]
            
        if not keys or not keys[0]:
            raise ValueError("No Gemini API keys found in environment variables. Check your .env file!")
            
        for key in keys:
            _clients.append(genai.Client(api_key=key))
            
    return _clients

import time
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError

@retry(stop=stop_after_attempt(20), wait=wait_exponential(multiplier=2, min=5, max=30))
def _embed_batch(client, texts: list[str]) -> list[list[float]]:
    response = client.models.embed_content(
        model='gemini-embedding-2',
        contents=texts
    )
    return [e.values for e in response.embeddings]

def get_embeddings_batch(texts: list[str], batch_size: int = 5) -> list[list[float]]:
    """Generates embeddings for a list of texts in batches to respect rate limits."""
    global _current_client_idx
    clients = _get_clients()
    
    all_embeddings = []
    
    try:
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Round-robin the keys for rate limit balancing
            client = clients[_current_client_idx]
            _current_client_idx = (_current_client_idx + 1) % len(clients)
            
            batch_embeddings = _embed_batch(client, batch)
            all_embeddings.extend(batch_embeddings)
            
            # Sleep aggressively to avoid Tokens-Per-Minute (TPM) exhaustion on Free Tier
            if i + batch_size < len(texts):
                time.sleep(3.5)
    except RetryError as e:
        raise Exception(f"Google Gemini API Quota Exhausted! We retried 5 times but Google blocked us. Either your daily quota is used up, or you hit the Tokens-Per-Minute limit.")
            
    return all_embeddings

def get_embedding(text: str) -> list[float]:
    """Generates a 768-dimensional embedding for a given single text."""
    return get_embeddings_batch([text])[0]
