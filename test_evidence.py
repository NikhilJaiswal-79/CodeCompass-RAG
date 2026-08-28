import sqlite3, time, threading
from chunker import get_language, extract_name
from tree_sitter import Parser
from graph_builder import _traverse_and_extract_edges

def test_single_file():
    lang = get_language('javascript')
    parser = Parser(lang)
    fp = 'data/repos/NikhilJaiswal-79-safestep-7f220bd3/client/src/pages/EvidenceCapture.jsx'
    with open(fp, 'rb') as f:
        source = f.read()
    
    print(f"File size: {len(source)} bytes", flush=True)
    tree = parser.parse(source)
    
    # Count nodes
    count = 0
    stack = [tree.root_node]
    max_depth = 0
    depth_stack = [(tree.root_node, 0)]
    while depth_stack:
        node, depth = depth_stack.pop()
        count += 1
        if depth > max_depth:
            max_depth = depth
        for child in node.children:
            depth_stack.append((child, depth + 1))
    print(f"AST nodes: {count}, max depth: {max_depth}", flush=True)
    
    conn = sqlite3.connect(':memory:')
    c = conn.cursor()
    c.execute('CREATE TABLE nodes (id TEXT PRIMARY KEY, name TEXT, type TEXT, file_path TEXT, pagerank_score REAL)')
    c.execute('CREATE TABLE edges (source_id TEXT, target_name TEXT, edge_type TEXT, line_number INTEGER)')
    
    start = time.time()
    _traverse_and_extract_edges(tree.root_node, source, 'javascript', 'file_test', fp, c)
    elapsed = time.time() - start
    nodes = c.execute("SELECT count(*) FROM nodes").fetchone()[0]
    edges = c.execute("SELECT count(*) FROM edges").fetchone()[0]
    print(f"Done in {elapsed:.3f}s. Nodes: {nodes}, Edges: {edges}", flush=True)

# Test in main thread first
print("=== MAIN THREAD ===", flush=True)
test_single_file()

# Test in a thread
print("\n=== BACKGROUND THREAD ===", flush=True)
t = threading.Thread(target=test_single_file)
t.start()
t.join(timeout=15)
if t.is_alive():
    print("THREAD HUNG!", flush=True)
else:
    print("Thread completed OK", flush=True)
