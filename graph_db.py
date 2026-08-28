import sqlite3
import os

def get_graph_db_connection(repo_id: str):
    """
    Returns a connection to the SQLite graph database for a specific repository.
    Creates the database and schema if it doesn't exist.
    """
    repos_dir = os.path.join(os.path.dirname(__file__), "data", "repos")
    os.makedirs(repos_dir, exist_ok=True)
    
    db_path = os.path.join(repos_dir, f"{repo_id}_graph.db")
    conn = sqlite3.connect(db_path)
    
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON")
    
    _initialize_schema(conn)
    return conn

def _initialize_schema(conn: sqlite3.Connection):
    """
    Initializes the nodes and edges tables for the dependency graph.
    """
    cursor = conn.cursor()
    
    # Nodes can be files, functions, or classes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS nodes (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT NOT NULL, -- 'file', 'function', 'class'
        file_path TEXT NOT NULL,
        pagerank_score REAL DEFAULT 0.15
    )
    """)
    
    # Edges represent relationships (calls, imports, inherits)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS edges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id TEXT NOT NULL,
        target_name TEXT NOT NULL,
        edge_type TEXT NOT NULL, -- 'calls', 'imports', 'inherits'
        line_number INTEGER,
        FOREIGN KEY (source_id) REFERENCES nodes (id) ON DELETE CASCADE
    )
    """)
    
    # Indices for faster lookup
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON edges (source_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON edges (target_name)")
    
    conn.commit()
