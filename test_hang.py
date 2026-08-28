import time
import os
from tree_sitter import Parser
from chunker import get_language
from utils import get_files_to_index

files = get_files_to_index('data/repos/NikhilJaiswal-79-safestep-b6eb8840')

for i, file_path in enumerate(files):
    if not (file_path.endswith('.js') or file_path.endswith('.jsx')): continue
    lang = get_language('javascript')
    parser = Parser(lang)
    
    print(f"Testing {i}: {file_path}", flush=True)
    try:
        with open(file_path, "rb") as f:
            source = f.read()
        parser.parse(source)
    except Exception as e:
        print(f"Failed {i}: {e}")