import os
import json
import shutil
from guidelines import process_guidelines

def run_test():
    test_repo_id = "test_guidelines_repo"
    test_repo_dir = "test_dummy_repo"
    
    # 1. Create a dummy repo directory and CONTRIBUTING.md
    os.makedirs(test_repo_dir, exist_ok=True)
    
    contributing_content = """
    # Contributing to ContribLens
    
    Welcome! Please follow these rules:
    
    ## Coding Standards
    - All Python code must be formatted using Black.
    - Please include docstrings for all public functions using the Google style guide.
    
    ## Testing
    - You must write unit tests for any new features.
    - We use pytest. Run `pytest` before submitting a PR.
    - Code coverage must not drop below 90%.
    
    ## Process
    - All PRs must have at least one approving review.
    - Commit messages must follow conventional commits (e.g., feat: add button).
    """
    
    with open(os.path.join(test_repo_dir, "CONTRIBUTING.md"), "w") as f:
        f.write(contributing_content)
        
    print("--- Extracting Rules with Groq ---")
    process_guidelines(test_repo_id, test_repo_dir)
    
    # 2. Check the output
    repos_dir = os.path.join(os.path.dirname(__file__), "data", "repos")
    rules_path = os.path.join(repos_dir, f"{test_repo_id}_rules.json")
    
    print("\n--- Output JSON ---")
    if os.path.exists(rules_path):
        with open(rules_path, "r") as f:
            rules = json.load(f)
            print(json.dumps(rules, indent=2))
    else:
        print("Error: Rules JSON not found!")
        
    # Cleanup
    shutil.rmtree(test_repo_dir)

if __name__ == "__main__":
    run_test()
