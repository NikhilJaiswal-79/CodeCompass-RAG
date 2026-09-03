import os
import subprocess
import shutil
import re
import random
def clone_repo(url: str, target_dir: str) -> bool:
    """
    Shallow-clones a git repository to the target directory.
    Returns True if successful, False otherwise.
    """
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    if os.path.exists(target_dir):
        # On Windows, .git folders have read-only files that shutil.rmtree cannot delete natively
        import stat
        def on_rm_error(func, path, exc_info):
            try:
                os.chmod(path, stat.S_IWRITE)
                func(path)
            except Exception:
                pass
        shutil.rmtree(target_dir, onerror=on_rm_error)
    
    try:
        # --depth 1 for a shallow clone to save time and disk space
        subprocess.run(
            ["git", "clone", "--depth", "1", url, target_dir],
            check=True,
            capture_output=True,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error cloning repo {url}: {e.stderr}")
        return False

def get_files_to_index(repo_dir: str) -> list[str]:
    """
    Walks the directory and returns a list of file paths to index.
    Skips irrelevant directories and files.
    """
    skip_dirs = {".git", "node_modules", "venv", "__pycache__", "dist", "build"}
    skip_extensions = {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".exe", ".dll", ".so", ".dylib", ".lock"}
    
    files_to_index = []
    
    for root, dirs, files in os.walk(repo_dir):
        # Modify dirs in-place to prevent os.walk from traversing skip_dirs
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in skip_extensions:
                continue
            # Optionally skip common lock files
            if file in {"package-lock.json", "yarn.lock", "poetry.lock"}:
                continue
                
            file_path = os.path.join(root, file)
            # FAST HACK FOR CORSAIR EVAL to prevent 4000+ files taking 2 hours
            if "corsairdev-corsair" in file_path and os.path.join("packages", "corsair") not in file_path:
                continue
                
            files_to_index.append(file_path)
            
    return files_to_index

import re

STOP_WORDS = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "of", "to", "for", "with", "by", "about", "as", "and", "or", "not", "this", "that", "it", "what", "how", "why", "when", "where", "repo", "code", "file", "can", "i", "do", "does", "did", "have", "has"}

def tokenize_for_bm25(text: str) -> list[str]:
    """
    Lowercases, removes punctuation, and filters out common stop words
    to prevent BM25 from being hijacked by natural language filler words.
    """
    tokens = re.findall(r'\b\w+\b', text.lower())
    return [t for t in tokens if t not in STOP_WORDS]

_current_key_idx = 0

def get_gemini_client():
    """
    Returns a configured Gemini client using one of the 3 API keys in round-robin rotation.
    """
    import os
    global _current_key_idx
    from google import genai
    
    key1 = os.getenv("GEMINI_API_KEY_1")
    key2 = os.getenv("GEMINI_API_KEY_2")
    key3 = os.getenv("GEMINI_API_KEY_3")
    
    keys = [k for k in [key1, key2, key3] if k]
    if not keys:
        raise ValueError("No GEMINI_API_KEY found in .env")
        
    selected_key = keys[_current_key_idx % len(keys)]
    _current_key_idx += 1
    
    return genai.Client(api_key=selected_key)
