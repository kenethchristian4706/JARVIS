"""
evaluate.py

This script evaluates the offline tool selection PoC.
It runs the test queries, calculates overall accuracy, average similarity scores,
lists failed predictions, and constructs a compact filtered confusion matrix
for active tools to analyze performance.
"""

import sys
import time
from collections import defaultdict
import numpy as np

# Adjust path to import from the current directory if running directly
from test_queries import TEST_QUERIES
from selector import select_tool





def run_evaluation():
    print("=" * 60)
    print("AETHER OFFLINE TOOL SELECTION EVALUATION BENCHMARK")
    print("=" * 60)
    
    total = len(TEST_QUERIES)
    correct = 0
    failures = []
    
    scores_correct = []
    scores_incorrect = []
    scores_all = []
    latencies = []
    
    # Store predictions for the confusion matrix
    # Format: matrix[expected][predicted] = count
    confusion_data = defaultdict(lambda: defaultdict(int))
    active_tools = set()

    print(f"Running {total} test queries...\n")
    start_time = time.time()
    
    for i, (query, expected) in enumerate(TEST_QUERIES, 1):
        start = time.perf_counter()
        try:
            result = select_tool(query)
            latency = (time.perf_counter() - start) * 1000
            latencies.append(latency)
            predicted = result["selected_tool"]
            score = result["score"]
            
            print(
                f"{query}\n"
                f"Expected: {expected}\n"
                f"Predicted: {predicted}\n"
                f"Score: {score:.4f}\n"
                f"Latency: {latency:.2f} ms\n"
            )
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            latencies.append(latency)
            print(f"Error evaluating query '{query}': {e}", file=sys.stderr)
            failures.append({
                "query": query,
                "expected": expected,
                "predicted": "ERROR",
                "score": 0.0,
                "error": str(e)
            })
            confusion_data[expected]["ERROR"] += 1
            active_tools.add(expected)
            active_tools.add("ERROR")
            continue
            
        scores_all.append(score)
        confusion_data[expected][predicted] += 1
        active_tools.add(expected)
        active_tools.add(predicted)
        
        is_correct = (predicted == expected)
        if is_correct:
            correct += 1
            scores_correct.append(score)
        else:
            scores_incorrect.append(score)
            failures.append({
                "query": query,
                "expected": expected,
                "predicted": predicted,
                "score": score
            })
            
    elapsed_time = time.time() - start_time
    accuracy = (correct / total) * 100
    
    avg_score_all = np.mean(scores_all) if scores_all else 0.0
    avg_score_correct = np.mean(scores_correct) if scores_correct else 0.0
    avg_score_incorrect = np.mean(scores_incorrect) if scores_incorrect else 0.0
    avg_latency = np.mean(latencies) if latencies else 0.0
    
    # Render Evaluation Summary
    print("\n" + "-" * 60)
    print("METRICS SUMMARY")
    print("-" * 60)
    print(f"Total Test Queries:        {total}")
    print(f"Correct Predictions:       {correct}")
    print(f"Failed Predictions:        {len(failures)}")
    print(f"Overall Accuracy:          {accuracy:.2f}% (Target: >=85%, Goal: >=90%)")
    print(f"Average Similarity Score:  {avg_score_all:.4f}")
    print(f"  - Correct predictions:   {avg_score_correct:.4f}")
    print(f"  - Failed predictions:    {avg_score_incorrect:.4f}")
    print(f"Average Latency:           {avg_latency:.2f} ms")
    print(f"Execution Time:            {elapsed_time:.3f} seconds ({elapsed_time/total:.4f}s per query)")
    print("-" * 60)
    
    # Render Failures Table
    if failures:
        print("\n" + "=" * 60)
        print("FAILED PREDICTIONS DETAIL")
        print("=" * 60)
        print(f"{'Query':<45} | {'Expected':<18} | {'Predicted':<18} | {'Score':<6}")
        print("-" * 93)
        for fail in failures:
            query_trunc = fail["query"] if len(fail["query"]) <= 42 else fail["query"][:39] + "..."
            pred_val = fail["predicted"]
            if "error" in fail:
                pred_val = f"ERR ({fail['error'][:10]})"
            print(f"{query_trunc:<45} | {fail['expected']:<18} | {pred_val:<18} | {fail['score']:.4f}")
        print("=" * 60)
    else:
        print("\n[SUCCESS] Perfect Score! Zero failed predictions.")
        
    # Render Active Confusion Matrix
    print("\n" + "=" * 60)
    print("CONFUSION MATRIX (ACTIVE TOOLS ONLY)")
    print("=" * 60)
    print("Note: Grid limited to tools appearing as expected or predicted labels.")
    print("Columns = Predicted, Rows = Expected\n")
    
    # Sort active tools list for consistency
    sorted_active = sorted(list(active_tools))
    
    # Calculate column widths based on label lengths
    col_width = max(len(label) for label in sorted_active) if sorted_active else 10
    col_width = max(col_width, 6) # min width
    
    # Print header row
    header = f"{'Expected Tool':<25} |"
    for label in sorted_active:
        header += f" {label[:col_width]:^{col_width}} |"
    print(header)
    print("-" * len(header))
    
    # Print data rows
    for row_label in sorted_active:
        row_str = f"{row_label:<25} |"
        for col_label in sorted_active:
            count = confusion_data[row_label][col_label]
            count_str = str(count) if count > 0 else "-"
            row_str += f" {count_str:^{col_width}} |"
        print(row_str)
        
    print("=" * 60)
    
    # Exit code based on accuracy threshold
    if accuracy >= 85.0:
        print("\n[SUCCESS] Benchmark SUCCESS: Accuracy meets or exceeds 85.0% threshold.")
        sys.exit(0)
    else:
        print("\n[FAILURE] Benchmark FAILED: Accuracy is below the 85.0% threshold.")
        sys.exit(1)

if __name__ == "__main__":
    run_evaluation()
