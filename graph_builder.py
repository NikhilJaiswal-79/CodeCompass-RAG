import os
import json
import subprocess
import sys
from chunker import get_language, extract_name
from graph_db import get_graph_db_connection

def extract_and_store_graph(repo_id: str, files: list[str]):
    """
    Parses all files in the repository to extract function calls and imports,
    and stores them as a dependency graph in SQLite.
    Runs tree-sitter in a subprocess to isolate C-level segfaults.
    """
    print(f"[DEBUG] Started extract_and_store_graph for {repo_id}")
    conn = get_graph_db_connection(repo_id)
    cursor = conn.cursor()
    
    # First pass: Clear existing data for this repo to allow re-indexing if needed
    cursor.execute("DELETE FROM edges")
    cursor.execute("DELETE FROM nodes")
    print(f"[DEBUG] DB tables cleared for {repo_id}")
    
    extractor_path = os.path.join(os.path.dirname(__file__), "tree_sitter_extractor.py")
    for i, file_path in enumerate(files):
        print(f"[DEBUG] Processing {i}/{len(files)}: {file_path}", flush=True)
        if file_path.endswith(".py"):
            lang_name = "python"
        elif file_path.endswith(".js") or file_path.endswith(".jsx"):
            lang_name = "javascript"
        elif file_path.endswith(".ts") or file_path.endswith(".tsx"):
            lang_name = "typescript"
        else:
            continue
            
        try:
            result = subprocess.run(
                [sys.executable, extractor_path, file_path, lang_name],
                capture_output=True,
                text=True,
                check=True
            )
            data = json.loads(result.stdout)
            nodes_data = data.get("nodes", [])
            edges_data = data.get("edges", [])
        except subprocess.CalledProcessError as e:
            print(f"[WARNING] Skipping {file_path} due to extraction crash (Exit code: {e.returncode})", flush=True)
            continue
        except Exception as e:
            print(f"[WARNING] Skipping {file_path} due to error: {e}", flush=True)
            continue
            
        # PHASE 2: Write pure Python data to SQLite
        file_id = f"file_{file_path}"
        cursor.execute("INSERT OR IGNORE INTO nodes (id, name, type, file_path) VALUES (?, ?, ?, ?)",
                       (file_id, os.path.basename(file_path), "file", file_path))
        
        for node_row in nodes_data:
            cursor.execute("INSERT OR IGNORE INTO nodes (id, name, type, file_path) VALUES (?, ?, ?, ?)",
                           (node_row["id"], node_row["name"], node_row["type"], node_row["file_path"]))
        
        for edge_row in edges_data:
            cursor.execute("INSERT INTO edges (source_id, target_name, edge_type, line_number) VALUES (?, ?, ?, ?)",
                           (edge_row["source_id"], edge_row["target_name"], edge_row["edge_type"], edge_row["line_number"]))
        
    print(f"[DEBUG] Committing AST nodes/edges to SQLite for {repo_id}")
    conn.commit()
    
    # Calculate PageRank
    print(f"[DEBUG] Calculating PageRank for {repo_id}")
    calculate_pagerank(conn)
    print(f"[DEBUG] Finished calculate_pagerank for {repo_id}")
    
    conn.close()

def calculate_pagerank(conn):
    """
    Calculates PageRank for all nodes and updates the database.
    """
    print(f"[DEBUG] Entering calculate_pagerank")
    import networkx as nx
    
    cursor = conn.cursor()
    
    # 1. Load nodes and edges into NetworkX
    G = nx.DiGraph()
    
    cursor.execute("SELECT id, name FROM nodes")
    nodes = cursor.fetchall()
    
    # We need a mapping from node name to node ID because our edges table stores target_name (loose coupling)
    name_to_ids = {}
    for node_id, name in nodes:
        G.add_node(node_id)
        if name not in name_to_ids:
            name_to_ids[name] = []
        name_to_ids[name].append(node_id)
        
    cursor.execute("SELECT source_id, target_name FROM edges")
    edges = cursor.fetchall()
    
    for source_id, target_name in edges:
        # Resolve target_name to IDs
        if target_name in name_to_ids:
            targets = name_to_ids[target_name]
            
            # Anti-Cartesian Explosion Heuristic:
            if len(targets) > 5:
                continue
                
            for target_id in targets:
                G.add_edge(source_id, target_id)
                
    if len(G.nodes) == 0:
        return
        
    # 2. Run PageRank
    try:
        pagerank_scores = nx.pagerank(G, alpha=0.85)
    except Exception as e:
        print(f"PageRank calculation failed: {e}")
        return
        
    # 3. Update database
    for node_id, score in pagerank_scores.items():
        cursor.execute("UPDATE nodes SET pagerank_score = ? WHERE id = ?", (score, node_id))
    conn.commit()
    print(f"Calculated PageRank for {len(pagerank_scores)} nodes.")
