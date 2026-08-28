from sentence_transformers import SentenceTransformer

# Load embedding model once in memory
# We use all-MiniLM-L6-v2 as it's small and fast for testing
MODEL_NAME = 'all-MiniLM-L6-v2'
model = None

def get_embedding(text: str) -> list[float]:
    """Generates an embedding for a given text."""
    global model
    if model is None:
        model = SentenceTransformer(MODEL_NAME)
    
    # Convert numpy array to list for ChromaDB
    return model.encode(text).tolist()
