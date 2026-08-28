import os
from chunker import parse_file_to_chunks

def run_test():
    # Create a dummy Java file
    java_code = """
package com.example;

public class DatabaseManager {
    private String connectionString;

    public DatabaseManager(String connStr) {
        this.connectionString = connStr;
    }

    public void connect() {
        System.out.println("Connecting to " + connectionString);
    }
    
    public void disconnect() {
        System.out.println("Disconnecting");
    }
}
"""
    with open("dummy.java", "w") as f:
        f.write(java_code)
        
    print("--- Testing Java AST Parsing ---")
    chunks = parse_file_to_chunks("dummy.java")
    
    print(f"Total chunks extracted: {len(chunks)}\n")
    for i, c in enumerate(chunks):
        print(f"Chunk #{i+1}:")
        print(f"  Name: {c.name}")
        print(f"  Type: {c.chunk_type}")
        print(f"  Language: {c.language}")
        print(f"  Lines: {c.start_line} to {c.end_line}")
        print(f"  Content Preview: {c.content[:40]}...\n")

    # Cleanup
    if os.path.exists("dummy.java"):
        os.remove("dummy.java")

if __name__ == "__main__":
    run_test()
