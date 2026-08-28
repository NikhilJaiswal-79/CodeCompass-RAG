import chromadb
from chromadb.config import Settings
import os

# Create a data directory for ChromaDB local storage
DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "chroma")
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize ChromaDB client
# Using PersistentClient so collections survive restarts
chroma_client = chromadb.PersistentClient(path=DATA_DIR)

def get_or_create_collection(repo_id: str):
    """
    Gets or creates a ChromaDB collection for a specific repository.
    Namespaces the vector store by repo_id.
    """
    # ChromaDB collection names must be valid (no special chars like slashes).
    # We will sanitize the repo_id just in case.
    sanitized_name = "".join([c if c.isalnum() or c in "-_" else "_" for c in repo_id])
    
    # We use get_or_create_collection
    collection = chroma_client.get_or_create_collection(name=sanitized_name)
    return collection
