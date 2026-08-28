import json
from run_langsmith_experiment import predict_answer, retrieval_eval, generation_eval
from evaluator import EVAL_DATASET

# Find row 2
row2 = EVAL_DATASET[1]
print("Testing Question:", row2["question"])

print("Running predict_answer...")
pred = predict_answer({"question": row2["question"]})
print("Prediction Context Length:", len(pred.get("context", [])))

class DummyRun:
    def __init__(self, outputs):
        self.outputs = outputs

class DummyExample:
    def __init__(self, inputs, outputs):
        self.inputs = inputs
        self.outputs = outputs

run = DummyRun(pred)
example = DummyExample({"question": row2["question"]}, {"ground_truth": row2["ground_truth"], "ground_truth_files": row2["ground_truth_files"], "ground_truth_functions": row2["ground_truth_functions"]})

print("Running retrieval_eval...")
ret = retrieval_eval(run, example)
print("Retrieval Eval Result:", ret)

print("Running generation_eval...")
gen = generation_eval(run, example)
print("Generation Eval Result:", gen)
