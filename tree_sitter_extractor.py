import sys
import json
import os
from tree_sitter import Parser
from chunker import get_language, extract_name

def _extract_call_target_name(node, source_bytes: bytes, lang_name: str) -> str:
    if node.type == "identifier":
        return source_bytes[node.start_byte:node.end_byte].decode('utf-8', errors='replace')
        
    if lang_name == "python" and node.type == "attribute":
        attr_node = node.child_by_field_name("attribute")
        if attr_node:
            return source_bytes[attr_node.start_byte:attr_node.end_byte].decode('utf-8', errors='replace')
            
    if lang_name in ("javascript", "typescript") and node.type == "member_expression":
        prop_node = node.child_by_field_name("property")
        if prop_node:
            return source_bytes[prop_node.start_byte:prop_node.end_byte].decode('utf-8', errors='replace')
            
    text = source_bytes[node.start_byte:node.end_byte].decode('utf-8', errors='replace')
    if len(text) < 50 and "\n" not in text:
        return text.split(".")[-1]
    return None

def extract_graph_data(file_path: str, lang_name: str):
    language = get_language(lang_name)
    if not language:
        return {"nodes": [], "edges": []}
        
    parser = Parser(language)
    with open(file_path, "rb") as f:
        source_bytes = f.read()
        
    tree = parser.parse(source_bytes)
    
    nodes_data = []
    edges_data = []
    
    root_node = tree.root_node
    file_id = f"file_{file_path}"
    
    stack = [(root_node, False)]
    scope_stack = [file_id]
    
    while stack:
        node, visited = stack.pop()
        
        if visited:
            if node.type in ("function_definition", "class_definition", "function_declaration", "class_declaration", "method_definition"):
                name = extract_name(node, source_bytes)
                if name and name != "anonymous":
                    scope_stack.pop()
            continue
            
        current_scope = scope_stack[-1]
        pushed_scope = False
        
        if node.type in ("function_definition", "class_definition", "function_declaration", "class_declaration", "method_definition"):
            name = extract_name(node, source_bytes)
            if name and name != "anonymous":
                node_id = f"{file_path}::{name}::{node.start_point.row}"
                node_type = "function" if "function" in node.type or "method" in node.type else "class"
                nodes_data.append({"id": node_id, "name": name, "type": node_type, "file_path": file_path})
                scope_stack.append(node_id)
                current_scope = node_id
                pushed_scope = True
                
        if node.type in ("call", "call_expression"):
            function_node = node.child_by_field_name("function")
            if function_node:
                target_name = _extract_call_target_name(function_node, source_bytes, lang_name)
                if target_name:
                    edges_data.append({
                        "source_id": current_scope,
                        "target_name": target_name,
                        "edge_type": "calls",
                        "line_number": node.start_point.row + 1
                    })
                                   
        if lang_name == "python" and node.type in ("import_statement", "import_from_statement"):
            for child in node.children:
                if child.type in ("dotted_name", "identifier"):
                    target_name = source_bytes[child.start_byte:child.end_byte].decode('utf-8', errors='replace')
                    edges_data.append({
                        "source_id": current_scope,
                        "target_name": target_name,
                        "edge_type": "imports",
                        "line_number": node.start_point.row + 1
                    })
                                   
        if lang_name in ("javascript", "typescript") and node.type == "import_statement":
            source_node = node.child_by_field_name("source")
            if source_node:
                target_name = source_bytes[source_node.start_byte:source_node.end_byte].decode('utf-8', errors='replace').strip("\"'")
                edges_data.append({
                    "source_id": current_scope,
                    "target_name": target_name,
                    "edge_type": "imports",
                    "line_number": node.start_point.row + 1
                })
        
        if pushed_scope:
            stack.append((node, True))
            
        for child in reversed(node.children):
            stack.append((child, False))
            
    return {"nodes": nodes_data, "edges": edges_data}

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(1)
    file_path = sys.argv[1]
    lang_name = sys.argv[2]
    
    try:
        data = extract_graph_data(file_path, lang_name)
        print(json.dumps(data))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
