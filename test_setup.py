import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("--- Testing Setup ---")

# 1. Test ChromaDB
try:
    import chromadb
    client = chromadb.Client()
    collection = client.create_collection("test_collection")
    collection.add(
        documents=["This is a test document"],
        metadatas=[{"source": "test"}],
        ids=["id1"]
    )
    results = collection.query(query_texts=["test"], n_results=1)
    print("[SUCCESS] ChromaDB: Successfully created local collection, inserted, and queried.")
except Exception as e:
    print(f"[ERROR] ChromaDB Error: {e}")

# 2. Test Tree-sitter
try:
    import tree_sitter
    import tree_sitter_python as tspython
    from tree_sitter import Language, Parser

    # Setup Python parser
    PY_LANGUAGE = Language(tspython.language())
    parser = Parser(PY_LANGUAGE)
    
    # Parse a sample chunk
    source_code = b"def foo():\n    return 'bar'"
    tree = parser.parse(source_code)
    if tree.root_node.type == 'module':
        print("[SUCCESS] Tree-sitter: Successfully parsed Python snippet.")
    else:
        print("[ERROR] Tree-sitter Error: Did not parse root node as 'module'.")
except Exception as e:
    print(f"[ERROR] Tree-sitter Error: {e}")

# 3. Test sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    # Using a small, fast model for testing
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embedding = model.encode("This is a test sentence.")
    if len(embedding) > 0:
        print("[SUCCESS] Sentence-transformers: Successfully loaded model and generated embedding.")
except Exception as e:
    print(f"[ERROR] Sentence-transformers Error: {e}")

# 4. Test Groq API
try:
    from groq import Groq
    
    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key:
        client = Groq(api_key=groq_api_key)
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Say 'hello world' and nothing else.",
                }
            ],
            model="llama3-8b-8192",
        )
        print(f"[SUCCESS] Groq API: Successfully responded with -> '{chat_completion.choices[0].message.content}'")
    else:
        print("[WARN] Groq API: GROQ_API_KEY not found in .env, skipping test.")
except Exception as e:
    print(f"[ERROR] Groq API Error: {e}")

print("---------------------")
print("Setup testing complete.")
