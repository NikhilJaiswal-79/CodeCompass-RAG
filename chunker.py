import os
from pydantic import BaseModel
from tree_sitter import Language, Parser

class Chunk(BaseModel):
    file_path: str
    content: str
    start_line: int
    end_line: int
    name: str
    chunk_type: str
    language: str

LANGUAGES = {}

def get_language(lang_name: str) -> Language:
    if lang_name not in LANGUAGES:
        try:
            if lang_name == "python":
                import tree_sitter_python as tspython
                LANGUAGES["python"] = Language(tspython.language())
            elif lang_name in ("javascript", "typescript"):
                import tree_sitter_javascript as tsjs
                LANGUAGES[lang_name] = Language(tsjs.language())
            elif lang_name == "go":
                import tree_sitter_go as tsgo
                LANGUAGES["go"] = Language(tsgo.language())
            elif lang_name == "rust":
                import tree_sitter_rust as tsrust
                LANGUAGES["rust"] = Language(tsrust.language())
            elif lang_name == "java":
                import tree_sitter_java as tsjava
                LANGUAGES["java"] = Language(tsjava.language())
            elif lang_name == "cpp":
                import tree_sitter_cpp as tscpp
                LANGUAGES["cpp"] = Language(tscpp.language())
            elif lang_name == "c":
                import tree_sitter_c as tsc
                LANGUAGES["c"] = Language(tsc.language())
            elif lang_name == "c-sharp":
                import tree_sitter_c_sharp as tscsharp
                LANGUAGES["c-sharp"] = Language(tscsharp.language())
            elif lang_name == "ruby":
                import tree_sitter_ruby as tsruby
                LANGUAGES["ruby"] = Language(tsruby.language())
            elif lang_name == "php":
                import tree_sitter_php as tsphp
                LANGUAGES["php"] = Language(tsphp.language_php())
            elif lang_name == "scala":
                import tree_sitter_scala as tsscala
                LANGUAGES["scala"] = Language(tsscala.language())
            elif lang_name == "swift":
                import tree_sitter_swift as tsswift
                LANGUAGES["swift"] = Language(tsswift.language())
            elif lang_name == "kotlin":
                import tree_sitter_kotlin as tskotlin
                LANGUAGES["kotlin"] = Language(tskotlin.language())
            elif lang_name == "bash":
                import tree_sitter_bash as tsbash
                LANGUAGES["bash"] = Language(tsbash.language())
            elif lang_name == "html":
                import tree_sitter_html as tshtml
                LANGUAGES["html"] = Language(tshtml.language())
            elif lang_name == "css":
                import tree_sitter_css as tscss
                LANGUAGES["css"] = Language(tscss.language())
            elif lang_name == "json":
                import tree_sitter_json as tsjson
                LANGUAGES["json"] = Language(tsjson.language())
            elif lang_name == "yaml":
                import tree_sitter_yaml as tsyaml
                LANGUAGES["yaml"] = Language(tsyaml.language())
            elif lang_name == "sql":
                import tree_sitter_sql as tssql
                LANGUAGES["sql"] = Language(tssql.language())
        except Exception as e:
            print(f"Warning: Failed to load tree-sitter language '{lang_name}': {e}")
            return None
    return LANGUAGES.get(lang_name)

def get_language_from_ext(ext: str) -> str:
    ext_map = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
        ".cs": "c-sharp",
        ".rb": "ruby",
        ".php": "php",
        ".scala": "scala",
        ".swift": "swift",
        ".kt": "kotlin",
        ".sh": "bash",
        ".bash": "bash",
        ".html": "html",
        ".css": "css",
        ".json": "json",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".sql": "sql",
    }
    return ext_map.get(ext.lower())

def extract_name(node, source_bytes: bytes) -> str:
    name_node = node.child_by_field_name("name")
    if name_node:
        return source_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8", errors="replace")
    return "anonymous"

def parse_file_to_chunks(file_path: str) -> list[Chunk]:
    ext = os.path.splitext(file_path)[1]
    lang_name = get_language_from_ext(ext)
    
    if not lang_name:
        return []
        
    language = get_language(lang_name)
    if not language:
        return []
        
    parser = Parser(language)
    
    with open(file_path, "rb") as f:
        source_bytes = f.read()
        
    tree = parser.parse(source_bytes)
    chunks = []
    
    target_types = {
        "python": {"function_definition", "class_definition"},
        "javascript": {"function_declaration", "class_declaration", "method_definition"},
        "typescript": {"function_declaration", "class_declaration", "method_definition"},
        "go": {"function_declaration", "method_declaration"},
        "rust": {"function_item", "impl_item"},
        "java": {"method_declaration", "class_declaration"},
        "cpp": {"function_definition", "class_specifier", "struct_specifier"},
        "c": {"function_definition", "struct_specifier"},
        "c-sharp": {"method_declaration", "class_declaration", "struct_declaration"},
        "ruby": {"method", "class"},
        "php": {"function_definition", "method_declaration", "class_declaration"},
        "scala": {"class_definition", "object_definition", "function_definition"},
        "swift": {"function_declaration", "class_declaration", "struct_declaration"},
        "kotlin": {"function_declaration", "class_declaration", "object_declaration"},
        "bash": {"function_definition"}
    }
    
    types_for_lang = target_types.get(lang_name, set())
    
    # Fallback for data/markup languages (HTML, CSS, JSON, YAML) or parsing errors
    if not types_for_lang or tree.root_node.has_error:
        content = source_bytes.decode("utf-8", errors="replace")
        return [Chunk(
            file_path=file_path,
            content=content,
            start_line=1,
            end_line=content.count("\n") + 1,
            name=os.path.basename(file_path),
            chunk_type="file",
            language=lang_name
        )]
    
    def traverse(node):
        if node.type in types_for_lang:
            name = extract_name(node, source_bytes)
            content = source_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace")
            
            chunk = Chunk(
                file_path=file_path,
                content=content,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                name=name,
                chunk_type=node.type,
                language=lang_name
            )
            chunks.append(chunk)
            return
            
        for child in node.children:
            traverse(child)

    traverse(tree.root_node)
    
    # If the file had valid AST but no target nodes were found, return the whole file
    if not chunks:
        content = source_bytes.decode("utf-8", errors="replace")
        return [Chunk(
            file_path=file_path,
            content=content,
            start_line=1,
            end_line=content.count("\n") + 1,
            name=os.path.basename(file_path),
            chunk_type="file",
            language=lang_name
        )]
        
    return chunks
