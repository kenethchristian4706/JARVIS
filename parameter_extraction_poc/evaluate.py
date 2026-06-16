"""
evaluate.py

Runs the parameter extraction evaluation benchmark.
Launches the sidecar llama-server.exe, processes all test cases, measures latencies,
validates output schemas, checks parameter accuracy and hallucinations,
and prints a comprehensive terminal report.
"""

import sys
import time
from collections import defaultdict
import numpy as np

import extractor
from test_cases import TEST_CASES
from schemas import TOOL_REGISTRY

def is_hallucinated(extracted_params: dict, expected_params: dict, query_text: str) -> bool:
    """
    Determines if any extracted parameter is a hallucination.
    A hallucination occurs when the model outputs a non-null parameter value
    that is neither expected nor present in the user query text.
    """
    for k, v in extracted_params.items():
        if v is not None and v != "":
            # Case 1: Key is not expected to have a value (not in expected_params)
            if k not in expected_params:
                # If the value is not found in the raw query, it's a hallucination
                if str(v).lower() not in query_text.lower():
                    return True
            # Case 2: Key is expected, but value is incorrect
            else:
                expected_val = expected_params[k]
                if expected_val != v:
                    # If this wrong value is not in the raw query, it's a hallucination
                    if str(v).lower() not in query_text.lower():
                        return True
    return False

def are_params_equal(extracted: dict, expected: dict) -> bool:
    """
    Checks if extracted parameters match expected parameters, ignoring string case sensitivity.
    """
    if extracted.keys() != expected.keys():
        return False
    for k, v in extracted.items():
        expected_v = expected[k]
        if isinstance(v, str) and isinstance(expected_v, str):
            if v.lower() != expected_v.lower():
                return False
        else:
            if v != expected_v:
                return False
    return True

def run_evaluation():
    # 1. Start sidecar server
    print("=" * 70)
    print("AETHER OFFLINE PARAMETER EXTRACTION BENCHMARK")
    print("=" * 70)
    
    server_started = extractor.start_sidecar_server()
    if not server_started:
        print("[ERROR] Failed to start local sidecar server. Aborting evaluation.", file=sys.stderr)
        sys.exit(1)
        
    total_cases = len(TEST_CASES)
    json_valid_count = 0
    exact_match_count = 0
    hallucination_count = 0
    repaired_count = 0
    grammar_used_count = 0
    latencies = []
    failures = []
    
    # Track stats per tool
    # Structure: tool_stats[tool_name] = {"total": 0, "correct": 0}
    tool_stats = defaultdict(lambda: {"total": 0, "correct": 0})
    
    print(f"\nRunning {total_cases} parameter extraction test cases...\n")
    start_eval_time = time.time()
    
    try:
        for idx, (tool_name, query, expected_json) in enumerate(TEST_CASES, 1):
            tool_stats[tool_name]["total"] += 1
            print(f"[{idx}/{total_cases}] Tool: '{tool_name}' | Query: \"{query}\"")
            
            t_start = time.perf_counter()
            result = extractor.extract_parameters(tool_name, query)
            latency = time.perf_counter() - t_start
            latencies.append(latency)
            
            # Check JSON Validity
            # If error is a JSON decoding error, then it's invalid JSON.
            # Schema validation errors imply the JSON was syntactically valid but had wrong schema structure.
            is_json_valid = True
            if result["error"] and "JSON syntax error" in result["error"]:
                is_json_valid = False
                
            if is_json_valid:
                json_valid_count += 1
                
            # Track repair usage and grammar usage
            if result.get("was_repaired"):
                repaired_count += 1
            if result.get("grammar_used"):
                grammar_used_count += 1
                
            # Check for Hallucination
            hallucinated = False
            if is_json_valid:
                hallucinated = is_hallucinated(result["parameters"], expected_json, query)
                if hallucinated:
                    hallucination_count += 1
                    
            # Check Exact Match Accuracy
            # We compare extracted parameters to the expected ones.
            # Convert keys and values to strings or basic types to compare cleanly.
            extracted_params = result["parameters"]
            
            # For exact matching, make sure all expected keys exist and match extracted values
            is_exact_match = False
            if is_json_valid and not result["error"]:
                # Pydantic validation passed, check equality (case-insensitive for string values)
                is_exact_match = are_params_equal(extracted_params, expected_json)
                
            if is_exact_match:
                exact_match_count += 1
                tool_stats[tool_name]["correct"] += 1
                print(f"      [PASS] Extracted: {extracted_params}")
                print(f"             Latency: {latency:.4f}s | Grammar Used: {result.get('grammar_used')} | Repaired: {result.get('was_repaired')}")
            else:
                failures.append({
                    "tool": tool_name,
                    "query": query,
                    "expected": expected_json,
                    "extracted": extracted_params,
                    "raw": result["raw_response"],
                    "error": result["error"],
                    "hallucinated": hallucinated,
                    "was_repaired": result.get("was_repaired"),
                    "grammar_used": result.get("grammar_used"),
                    "latency": latency
                })
                print(f"      [FAIL] Expected: {expected_json} | Extracted: {extracted_params}")
                print(f"             Latency: {latency:.4f}s | Grammar Used: {result.get('grammar_used')} | Repaired: {result.get('was_repaired')}")
                if result["error"]:
                    print(f"             Error: {result['error']}")
            print()
            
    finally:
        # Guarantee server shutdown
        extractor.stop_sidecar_server()
        
    total_eval_time = time.time() - start_eval_time
    
    # Calculate percentages
    json_validity_rate = (json_valid_count / total_cases) * 100
    extraction_accuracy = (exact_match_count / total_cases) * 100
    hallucination_rate = (hallucination_count / total_cases) * 100
    
    avg_latency = np.mean(latencies) if latencies else 0.0
    max_latency = np.max(latencies) if latencies else 0.0
    min_latency = np.min(latencies) if latencies else 0.0

    # 2. Render Benchmark Report
    print("\n" + "=" * 70)
    print("BENCHMARK METRICS SUMMARY")
    print("=" * 70)
    print(f"Total Test Cases:          {total_cases}")
    print(f"JSON Validity Rate:        {json_validity_rate:.2f}% (Target: >=98%)")
    print(f"Extraction Accuracy:       {extraction_accuracy:.2f}% (Target: >=90%)")
    print(f"Hallucination Rate:        {hallucination_rate:.2f}% (Target: <5%)")
    print(f"Average Latency:           {avg_latency:.4f}s  (Target: <5s)")
    print(f"Latency Range:             {min_latency:.4f}s to {max_latency:.4f}s")
    print(f"Grammar Constraints Used:  {grammar_used_count} / {total_cases} cases")
    print(f"JSON Repair Required:      {repaired_count} / {total_cases} cases")
    print(f"Total Execution Time:      {total_eval_time:.2f} seconds")
    print("=" * 70)

    # 3. Render Per-Tool Performance
    print("\n" + "-" * 45)
    print(f"{'Tool Name':<25} | {'Accuracy':<15}")
    print("-" * 45)
    for tool_name, stats in sorted(tool_stats.items()):
        tool_acc = (stats["correct"] / stats["total"]) * 100
        stats_str = f"{stats['correct']}/{stats['total']}"
        print(f"{tool_name:<25} | {tool_acc:.1f}% ({stats_str})")
    print("-" * 45)

    # 4. Render Failures Detail
    if failures:
        print("\n" + "=" * 70)
        print("FAILED EXTRACTION DETAILS")
        print("=" * 70)
        for i, fail in enumerate(failures, 1):
            print(f"Failure #{i}")
            print(f"  Tool:         {fail['tool']}")
            print(f"  Query:        \"{fail['query']}\"")
            print(f"  Expected:     {fail['expected']}")
            print(f"  Extracted:    {fail['extracted']}")
            print(f"  Raw LLM Text: \"{fail['raw']}\"")
            if fail['error']:
                print(f"  Error:        {fail['error']}")
            print(f"  Grammar Used: {'Yes' if fail['grammar_used'] else 'No'}")
            print(f"  Was Repaired: {'Yes' if fail['was_repaired'] else 'No'}")
            print(f"  Hallucinated: {'Yes' if fail['hallucinated'] else 'No'}")
            print(f"  Latency:      {fail['latency']:.4f}s")
            print("-" * 50)
        print("=" * 70)
    else:
        print("\n[SUCCESS] Perfect Score! Zero extraction failures.")

    # 5. Check if targets met
    success = (
        json_validity_rate >= 98.0 and
        extraction_accuracy >= 90.0 and
        avg_latency < 5.0 and
        hallucination_rate < 5.0
    )
    
    if success:
        print("\n[SUCCESS] Extraction PoC meets all required success criteria.")
        sys.exit(0)
    else:
        print("\n[FAILURE] Extraction PoC failed to meet one or more success criteria.")
        sys.exit(1)

if __name__ == "__main__":
    run_evaluation()
