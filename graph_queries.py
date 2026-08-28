from graph_db import get_graph_db_connection

def get_callers(repo_id: str, target_name: str):
    """
    Finds all functions/files that call the target_name.
    Returns a list of dicts with caller node info.
    """
    conn = get_graph_db_connection(repo_id)
    cursor = conn.cursor()
    
    query = """
    SELECT n.name, n.type, n.file_path, e.line_number
    FROM edges e
    JOIN nodes n ON e.source_id = n.id
    WHERE e.target_name = ? AND e.edge_type = 'calls'
    """
    
    cursor.execute(query, (target_name,))
    results = cursor.fetchall()
    conn.close()
    
    return [
        {"caller_name": row[0], "caller_type": row[1], "file_path": row[2], "line_number": row[3]}
        for row in results
    ]

def get_callees(repo_id: str, source_name: str):
    """
    Finds all targets called by the source_name.
    Since we store source_id as <file>::<name>::<line>, we look for matching names.
    """
    conn = get_graph_db_connection(repo_id)
    cursor = conn.cursor()
    
    query = """
    SELECT e.target_name, e.line_number, n.file_path
    FROM edges e
    JOIN nodes n ON e.source_id = n.id
    WHERE n.name = ? AND e.edge_type = 'calls'
    """
    
    cursor.execute(query, (source_name,))
    results = cursor.fetchall()
    conn.close()
    
    return [
        {"callee_name": row[0], "line_number": row[1], "file_path": row[2]}
        for row in results
    ]

def get_importers(repo_id: str, target_module: str):
    """
    Finds all files/functions that import the target_module.
    """
    conn = get_graph_db_connection(repo_id)
    cursor = conn.cursor()
    
    query = """
    SELECT n.name, n.type, n.file_path, e.line_number
    FROM edges e
    JOIN nodes n ON e.source_id = n.id
    WHERE e.target_name = ? AND e.edge_type = 'imports'
    """
    
    cursor.execute(query, (target_module,))
    results = cursor.fetchall()
    conn.close()
    
    return [
        {"importer_name": row[0], "importer_type": row[1], "file_path": row[2], "line_number": row[3]}
        for row in results
    ]