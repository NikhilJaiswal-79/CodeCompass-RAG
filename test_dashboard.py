import sqlite3, time
from chunker import get_language, extract_name
from tree_sitter import Parser
from graph_builder import _traverse_and_extract_edges

lang = get_language('javascript')
parser = Parser(lang)
f = open('data/repos/NikhilJaiswal-79-safestep-7f220bd3/client/src/pages/Dashboard.jsx','rb')
source = f.read()
tree = parser.parse(source)

conn = sqlite3.connect(':memory:')
c = conn.cursor()
c.execute('CREATE TABLE nodes (id TEXT PRIMARY KEY, name TEXT, type TEXT, file_path TEXT, pagerank_score REAL)')
c.execute('CREATE TABLE edges (source_id TEXT, target_name TEXT, edge_type TEXT, line_number INTEGER)')

start = time.time()
_traverse_and_extract_edges(tree.root_node, source, 'javascript', 'file_dashboard', 'Dashboard.jsx', c)
elapsed = time.time() - start
print(f'Done in {elapsed:.3f}s')
nodes = c.execute("SELECT count(*) FROM nodes").fetchone()[0]
edges = c.execute("SELECT count(*) FROM edges").fetchone()[0]
print(f'Nodes: {nodes}, Edges: {edges}')
