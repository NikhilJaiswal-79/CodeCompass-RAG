import os
from chunker import parse_file_to_chunks

def create_sample_files():
    py_content = """
import os

class ExampleClass:
    \"\"\"This is an example class.\"\"\"
    
    def __init__(self, value):
        self.value = value
        
    @staticmethod
    def example_method():
        \"\"\"This is an example method.\"\"\"
        def nested_func():
            pass
        return "Hello"

def standalone_function():
    return 42
"""
    js_content = """
class MyJSClass {
    constructor(name) {
        this.name = name;
    }
    
    greet() {
        console.log(`Hello ${this.name}`);
    }
}

function myJSFunction() {
    return true;
}
"""
    with open("sample.py", "w") as f:
        f.write(py_content)
    with open("sample.js", "w") as f:
        f.write(js_content)

def test_chunker():
    create_sample_files()
    
    for file_name in ["sample.py", "sample.js"]:
        print(f"\n--- Testing Chunker on {file_name} ---")
        chunks = parse_file_to_chunks(file_name)
        
        print(f"Extracted {len(chunks)} chunks:")
        for i, chunk in enumerate(chunks, 1):
            print(f"\n[Chunk {i}]")
            print(f"Name: {chunk.name}")
            print(f"Type: {chunk.chunk_type}")
            print(f"Lines: {chunk.start_line} - {chunk.end_line}")
            print("Content:")
            print("-" * 20)
            print(chunk.content.strip())
            print("-" * 20)

    # Cleanup
    os.remove("sample.py")
    os.remove("sample.js")

if __name__ == "__main__":
    test_chunker()
