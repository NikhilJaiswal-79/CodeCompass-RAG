import time
import os
import sqlite3
from tree_sitter import Parser
from chunker import get_language
from utils import get_files_to_index
from graph_builder import _traverse_and_extract_edges

files = get_files_to_index('data/repos/NikhilJaiswal-79-safestep-b6eb8840')

conn = sqlite3.connect(':memory:')
cursor = conn.cursor()
cursor.execute("CREATE TABLE nodes (id TEXT PRIMARY KEY, name TEXT, type TEXT, file_path TEXT, pagerank_score REAL)")
cursor.execute("CREATE TABLE edges (source_id TEXT, target_name TEXT, edge_type TEXT, line_number INTEGER)")

for i, file_path in enumerate(files):
    if not (file_path.endswith('.js') or file_path.endswith('.jsx') or file_path.endswith('.py') or file_path.endswith('.ts') or file_path.endswith('.tsx')): continue
    lang = get_language('javascript' if file_path.endswith('.js') or file_path.endswith('.jsx') else 'python')
    parser = Parser(lang)
    
    print(f"Traversing {i}: {file_path}", flush=True)
    try:
        with open(file_path, "rb") as f:
            source = f.read()
        tree = parser.parse(source)
        file_id = f"file_{file_path}"
        _traverse_and_extract_edges(tree.root_node, source, 'javascript', file_id, file_path, cursor)
    except Exception as e:
        print(f"Failed {i}: {e}")
print("Finished!")
