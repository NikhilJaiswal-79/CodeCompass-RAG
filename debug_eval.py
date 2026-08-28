import os
from langsmith import Client
from run_langsmith_experiment import retrieval_eval, generation_eval

client = Client()
runs = list(client.list_runs(project_name="Corsair-Hybrid-0b874738", execution_order=1))

for run in runs:
    if run.outputs and "answer" in run.outputs:
        print(f"Testing on Run ID: {run.id}, Question: {run.inputs.get('question')}")
        example = client.read_example(run.reference_example_id)
        
        print("--- Testing retrieval_eval ---")
        ret_result = retrieval_eval(run, example)
        print("Result:", ret_result)
        
        print("\n--- Testing generation_eval ---")
        gen_result = generation_eval(run, example)
        print("Result:", gen_result)
        break
else:
    print("No finished runs found.")
