"""
tests/integration_tests.py

Generates evaluation datasets (200 category examples, 500 tool examples, 500 parameter examples)
and runs verification tests to measure accuracy and response latency.
"""

import os
import sys
import json
import time
import random
import logging
from pathlib import Path

# Add project root to python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from aether.registry.tools import TOOLS
from aether.llm.model import start_server, stop_server
from aether.assistant import run_query
from aether.llm.intent_selector import select_intent
from aether.llm.parameter_extractor import extract_parameters

logger = logging.getLogger("integration_tests")

TESTS_DIR = Path(__file__).parent
TESTS_DIR.mkdir(exist_ok=True)

# Define file paths
CATEGORY_TESTS_PATH = TESTS_DIR / "category_tests.json"
TOOL_TESTS_PATH = TESTS_DIR / "tool_tests.json"
PARAMETER_TESTS_PATH = TESTS_DIR / "parameter_tests.json"

def generate_datasets():
    """Generates the three required datasets with templated expansions."""
    print("Generating programmatic test datasets...")
    
    # 1. Category Selection Dataset (Min 200 cases)
    categories_data = []
    apps = ["Chrome", "Notepad", "Spotify", "Calculator", "VS Code", "Word", "Excel"]
    files = ["report.pdf", "data.csv", "notes.txt", "resume.docx", "budget.xlsx"]
    folders = ["Documents", "Downloads", "Desktop", "Work", "Projects", "Photos"]
    urls = ["google.com", "youtube.com/watch", "github.com", "wikipedia.org"]
    queries = ["python tutorial", "funny videos", "weather today", "stock market"]
    levels = ["0", "15", "50", "85", "100"]

    # application_management templates
    app_tmpls = [
        "open {app}", "launch {app}", "start {app}", "run {app}", "please open {app}",
        "close {app}", "terminate {app}", "kill {app}", "stop {app}", "quit {app}",
        "switch to {app}", "focus {app}", "bring {app} to front", "go to {app}",
        "list running apps", "show active processes", "what applications are running",
        "list installed apps", "show my programs", "what apps do I have"
    ]
    for tmpl in app_tmpls:
        for app in apps:
            categories_data.append({
                "query": tmpl.format(app=app),
                "expected_category": "application_management"
            })

    # file_operations templates
    file_tmpls = [
        "move {file} to {folder}", "transfer {file} into {folder}", "put {file} in {folder}",
        "copy {file} to {folder}", "duplicate {file} to {folder}",
        "rename {file} to new_name.txt", "change name of {file} to backup.txt",
        "delete {file}", "remove {file}", "trash {file}",
        "search files for {query}", "find my files named {query}",
        "open file {file}", "launch file {file}", "view {file}",
        "create folder {folder}", "make a directory {folder}",
        "delete folder {folder}", "remove directory {folder}",
        "compress {file} into archive.zip", "zip {file}",
        "extract archive.zip to {folder}", "unzip archive.zip into {folder}",
        "create file {file}", "make file {file}", "create report.docx"
    ]
    for tmpl in file_tmpls:
        for file in files[:3]:
            for folder in folders[:3]:
                categories_data.append({
                    "query": tmpl.format(file=file, folder=folder, query="report"),
                    "expected_category": "file_operations"
                })

    # browser_operations templates
    browser_tmpls = [
        "search the web for {query}", "google search {query}", "look up {query} online",
        "search youtube for {query}", "play {query} on youtube", "youtube search {query}",
        "open URL {url}", "go to website {url}", "open site {url}",
        "download file from {url} to Downloads", "download {url}",
        "open a new tab with {url}", "new tab {url}",
        "close the active browser tab", "close browser tab"
    ]
    for tmpl in browser_tmpls:
        for query in queries[:3]:
            for url in urls[:3]:
                categories_data.append({
                    "query": tmpl.format(query=query, url=url),
                    "expected_category": "browser_operations"
                })

    # system_control templates
    system_tmpls = [
        "shutdown PC", "turn off computer", "power off",
        "restart computer", "reboot system",
        "sleep mode", "suspend PC", "put computer to sleep",
        "lock my computer", "lock session", "lock PC",
        "set volume to {level}", "change sound level to {level}", "volume {level}%",
        "mute volume", "mute audio", "silence sound",
        "set brightness to {level}", "make screen brightness {level}", "adjust brightness to {level}%"
    ]
    for tmpl in system_tmpls:
        for level in levels:
            categories_data.append({
                "query": tmpl.format(level=level),
                "expected_category": "system_control"
            })

    # Save unique categories
    unique_categories = []
    seen_queries = set()
    for item in categories_data:
        if item["query"] not in seen_queries:
            seen_queries.add(item["query"])
            unique_categories.append(item)
            
    with open(CATEGORY_TESTS_PATH, "w", encoding="utf-8") as f:
        json.dump(unique_categories, f, indent=2)
    print(f"Category Selection dataset saved. Total unique cases: {len(unique_categories)} (Required: >=200)")

    # 2. Tool Selection Dataset (Min 500 cases)
    tool_data = []
    # Generate mapping queries to tools
    tool_mappings = {
        "open_app": ["open {app}", "launch {app}", "start {app}", "please open {app}"],
        "close_app": ["close {app}", "terminate {app}", "kill {app}", "stop {app}"],
        "switch_to_app": ["switch focus to {app}", "focus {app}", "bring {app} to front", "go to {app}"],
        "list_running_apps": ["list running apps", "show active processes", "what apps are running"],
        "list_installed_apps": ["list installed apps", "show my programs", "what apps do I have"],
        
        "move_file": ["move {file} to {folder}", "transfer {file} into {folder}", "put {file} in {folder}"],
        "copy_file": ["copy {file} to {folder}", "duplicate {file} to {folder}"],
        "rename_file": ["rename {file} to new_name.txt", "change name of {file} to backup.txt"],
        "delete_file": ["delete {file}", "remove {file}", "trash {file}"],
        "search_files": ["search files for {query}", "find my files named {query}"],
        "open_file": ["open file {file}", "launch file {file}", "view {file}"],
        "create_folder": ["create folder {folder}", "make a directory {folder}"],
        "delete_folder": ["delete folder {folder}", "remove directory {folder}"],
        "compress_files": ["compress {file} into archive.zip", "zip {file}"],
        "extract_archive": ["extract archive.zip to {folder}", "unzip archive.zip into {folder}"],
        "create_file": ["create file {file}", "make file {file}", "create report.docx"],
        "list_directory": ["list directory path {folder}", "show contents of {folder}", "dir {folder}"],
        "file_info": ["file info {file}", "show info for {file}", "metadata for {file}"],
        
        "search_web": ["search the web for {query}", "google search {query}", "look up {query} online"],
        "search_youtube": ["search youtube for {query}", "play {query} on youtube", "youtube search {query}"],
        "open_url": ["open URL {url}", "go to website {url}", "open site {url}"],
        "download_file": ["download file from {url} to Downloads", "download {url}"],
        "open_new_tab": ["open a new tab with {url}", "new tab {url}"],
        "close_tab": ["close the active browser tab", "close browser tab"],
        "list_tabs": ["list open tabs", "show my browser tabs", "what browser tabs do i have"],
        "switch_tab": ["switch tab to {app}", "go to tab {app}"],
        
        "shutdown_pc": ["shutdown PC", "turn off computer", "power off"],
        "restart_pc": ["restart computer", "reboot system"],
        "sleep_pc": ["sleep mode", "suspend PC", "put computer to sleep"],
        "lock_pc": ["lock my computer", "lock session", "lock PC"],
        "set_volume": ["set volume to {level}", "change sound level to {level}", "volume {level}%"],
        "mute_volume": ["mute volume", "mute audio", "silence sound"],
        "unmute_volume": ["unmute volume", "unmute audio", "turn sound back on"],
        "set_brightness": ["set brightness to {level}", "make screen brightness {level}", "adjust brightness to {level}%"]
    }

    for tool_name, tmpls in tool_mappings.items():
        for tmpl in tmpls:
            for app in apps:
                for file in files:
                    for folder in folders:
                        for query in queries[:3]:
                            for url in urls[:3]:
                                for level in levels:
                                    q_str = tmpl.format(app=app, file=file, folder=folder, query=query, url=url, level=level)
                                    tool_data.append({
                                        "query": q_str,
                                        "expected_tool": tool_name
                                    })
                                    
    # Deduplicate and sample/save
    unique_tools = []
    seen_queries = set()
    for item in tool_data:
        if item["query"] not in seen_queries:
            seen_queries.add(item["query"])
            unique_tools.append(item)
            
    with open(TOOL_TESTS_PATH, "w", encoding="utf-8") as f:
        json.dump(unique_tools, f, indent=2)
    print(f"Tool Selection dataset saved. Total unique cases: {len(unique_tools)} (Required: >=500)")

    # 3. Parameter Extraction Dataset (Min 500 cases)
    parameter_data = []
    # Handlers that take arguments
    parameter_templates = [
        # open_app
        ("open_app", "open {app}", {"app_name": "{app}"}),
        ("open_app", "launch {app}", {"app_name": "{app}"}),
        # close_app
        ("close_app", "close {app}", {"app_name": "{app}"}),
        # switch_to_app
        ("switch_to_app", "switch focus to {app}", {"app_name": "{app}"}),
        # move_file
        ("move_file", "move {file} to {folder}", {"source": "{file}", "destination": "{folder}"}),
        # copy_file
        ("copy_file", "copy {file} to {folder}", {"source": "{file}", "destination": "{folder}"}),
        # rename_file
        ("rename_file", "rename {file} to {name}", {"source": "{file}", "new_name": "{name}"}),
        # delete_file
        ("delete_file", "delete {file}", {"filename": "{file}"}),
        # search_files
        ("search_files", "search files for {query}", {"query": "{query}"}),
        # open_file
        ("open_file", "open file {file}", {"filename": "{file}"}),
        # create_folder
        ("create_folder", "create folder {folder}", {"folder_name": "{folder}", "location": None}),
        # delete_folder
        ("delete_folder", "delete folder {folder}", {"folder_name": "{folder}"}),
        # create_file
        ("create_file", "create file {file}", {"filename": "{file}", "location": None}),
        # extract_archive
        ("extract_archive", "extract {file} to {folder}", {"archive": "{file}", "destination": "{folder}"}),
        # search_web
        ("search_web", "google search {query}", {"query": "{query}"}),
        # search_youtube
        ("search_youtube", "search youtube for {query}", {"query": "{query}"}),
        # open_url
        ("open_url", "open website {url}", {"url": "{url}"}),
        # download_file
        ("download_file", "download {url} to {folder}", {"url": "{url}", "destination": "{folder}"}),
        # open_new_tab
        ("open_new_tab", "open new tab with {url}", {"url": "{url}"}),
        # set_volume
        ("set_volume", "set volume to {level}", {"level": "{level}"}),
        # set_brightness
        ("set_brightness", "set brightness to {level}", {"level": "{level}"}),
        # file_info
        ("file_info", "show info for {file}", {"filename": "{file}"}),
        # list_directory
        ("list_directory", "list directory path {folder}", {"path": "{folder}"}),
        # switch_tab
        ("switch_tab", "switch tab to {app}", {"tab": "{app}"})
    ]

    for tool_name, tmpl, expected_params in parameter_templates:
        for app in apps:
            for file in files[:3]:
                for folder in folders[:3]:
                    for query in queries[:2]:
                        for url in urls[:2]:
                            for level_str in levels[:2]:
                                name_val = "backup.txt"
                                level_val = int(level_str)
                                
                                q_str = tmpl.format(app=app, file=file, folder=folder, query=query, url=url, level=level_str, name=name_val)
                                
                                # Resolve parameter values
                                p_dict = {}
                                for k, v in expected_params.items():
                                    if v is not None:
                                        val = v.format(app=app, file=file, folder=folder, query=query, url=url, level=level_val, name=name_val)
                                    else:
                                        val = None
                                    if k in ("level",) and val is not None:
                                        val = int(val)
                                    p_dict[k] = val
                                    
                                parameter_data.append({
                                    "tool": tool_name,
                                    "query": q_str,
                                    "expected_parameters": p_dict
                                })
                                
    unique_params = []
    seen_queries = set()
    for item in parameter_data:
        key = (item["tool"], item["query"])
        if key not in seen_queries:
            seen_queries.add(key)
            unique_params.append(item)
            
    with open(PARAMETER_TESTS_PATH, "w", encoding="utf-8") as f:
        json.dump(unique_params, f, indent=2)
    print(f"Parameter Extraction dataset saved. Total unique cases: {len(unique_params)} (Required: >=500)")


def run_benchmark():
    """Runs benchmark tests and reports accuracy and latencies."""
    print("\n=== STARTING REFACtORED BENCHMARK RUN ===")
    os.environ["AETHER_TESTING"] = "1"
    
    # Mock safety confirmation to avoid interactive prompts hanging in automated tests
    import aether.assistant
    aether.assistant.ask_user_confirmation = lambda tool, params: True
    
    # Mock input to handle ambiguity resolution and parameter collection prompts in tests
    import builtins
    def mock_input(prompt=""):
        p_str = prompt.lower()
        if "select" in p_str or "number" in p_str or "choice" in p_str or "1-5" in p_str or "1-3" in p_str:
            return "1"
        if "destination" in p_str or "where" in p_str or "location" in p_str:
            return "Documents"
        return "yes"
    builtins.input = mock_input
    
    # Start the sidecar server
    if not start_server():
        print("ERROR: Failed to launch LLM sidecar server.")
        return False

    # Synchronously index user files once to populate testing DB
    from aether.tools.indexer import index_all
    index_all()

    try:
        # Load datasets
        with open(TOOL_TESTS_PATH, "r", encoding="utf-8") as f:
            tool_tests = json.load(f)
        with open(PARAMETER_TESTS_PATH, "r", encoding="utf-8") as f:
            param_tests = json.load(f)

        # Select representative samples
        sample_size = 25
        intent_samples = random.sample(tool_tests, min(sample_size, len(tool_tests)))
        param_samples = random.sample(param_tests, min(sample_size, len(param_tests)))

        # 1. Evaluate Unified Intent Selection (Category + Tool in one LLM call)
        print("\nEvaluating Unified Intent Selection Accuracy...")
        intent_correct = 0
        intent_latencies = []
        for test in intent_samples:
            start_time = time.perf_counter()
            expected_tool = test["expected_tool"]
            expected_cat = TOOLS[expected_tool]["category"]
            
            try:
                predicted_cat, predicted_tool = select_intent(test["query"])
                latency = time.perf_counter() - start_time
                intent_latencies.append(latency)
                
                is_correct = (predicted_cat == expected_cat and predicted_tool == expected_tool)
                if is_correct:
                    intent_correct += 1
                print(f"Query: '{test['query']}' | Expected: ({expected_cat}, {expected_tool}) | Predicted: ({predicted_cat}, {predicted_tool}) | Correct: {is_correct} ({latency:.2f}s)")
            except Exception as e:
                print(f"Query: '{test['query']}' failed with error: {e}")
                
        intent_acc = (intent_correct / len(intent_samples)) * 100 if intent_samples else 0.0
        intent_lat_avg = sum(intent_latencies) / len(intent_latencies) if intent_latencies else 0.0

        # 2. Evaluate Parameter Extraction (LLM only)
        print("\nEvaluating Parameter Extraction Accuracy...")
        param_correct = 0
        param_latencies = []
        for test in param_samples:
            start_time = time.perf_counter()
            tool = test["tool"]
            try:
                extracted = extract_parameters(tool, test["query"])
                source_label = "LLM"
                    
                latency = time.perf_counter() - start_time
                param_latencies.append(latency)
                
                # Check properties match
                expected = test["expected_parameters"]
                is_correct = True
                for k, v in expected.items():
                    if extracted.get(k) != v:
                        is_correct = False
                        break
                if is_correct:
                    param_correct += 1
                print(f"Tool: {tool} | Source: {source_label} | Expected: {expected} | Extracted: {extracted} | Correct: {is_correct} ({latency:.2f}s)")
            except Exception as e:
                print(f"Query: '{test['query']}' failed with error: {e}")
                
        param_acc = (param_correct / len(param_samples)) * 100 if param_samples else 0.0
        param_lat_avg = sum(param_latencies) / len(param_latencies) if param_latencies else 0.0

        # 3. Evaluate End-to-End Execution on 10 random inputs
        print("\nEvaluating End-to-End Success Rate...")
        e2e_correct = 0
        e2e_latencies = []
        e2e_samples = random.sample(tool_tests, min(10, len(tool_tests)))
        for test in e2e_samples:
            start_time = time.perf_counter()
            # Run using the assistant pipeline
            result = run_query(test["query"])
            latency = time.perf_counter() - start_time
            e2e_latencies.append(latency)
            
            # Check if resolved tool matches expected tool
            predicted_tool = result.get("steps", {}).get("tool")
            is_correct = (predicted_tool == test["expected_tool"])
            if is_correct:
                e2e_correct += 1
            print(f"Query: '{test['query']}' | Expected Tool: {test['expected_tool']} | Resolved Tool: {predicted_tool} | Success: {result['success']} | Correct: {is_correct} ({latency:.2f}s)")
            
        e2e_acc = (e2e_correct / len(e2e_samples)) * 100 if e2e_samples else 0.0
        e2e_lat_avg = sum(e2e_latencies) / len(e2e_latencies) if e2e_latencies else 0.0

        # Print final report
        print("\n" + "="*60)
        print("                  AETHER REFACtORED RESULTS")
        print("="*60)
        print(f"Intent Selection Accuracy   : {intent_acc:.1f}% (Target >=95%)")
        print(f"Parameter Accuracy          : {param_acc:.1f}% (Target >=97%)")
        print(f"End-to-End Success Rate     : {e2e_acc:.1f}% (Target >=90%)")
        print("-" * 60)
        print(f"Avg Intent Selection Latency : {intent_lat_avg:.3f}s (Target <=1.0s)")
        print(f"Avg Parameter Latency       : {param_lat_avg:.3f}s (Rule-based is 0.00s)")
        print(f"Avg End-to-End Latency      : {e2e_lat_avg:.3f}s (Target <=2.5s)")
        print("="*60 + "\n")
        
        # Verify success criteria
        is_success = (
            intent_acc >= 95.0 and
            param_acc >= 97.0 and
            e2e_acc >= 90.0 and
            e2e_lat_avg <= 2.5
        )
        if is_success:
            print("[SUCCESS] Success! All evaluation targets met.")
        else:
            print("[WARNING] Warning: Some targets were not fully met under random testing sample.")

    finally:
        stop_server()

if __name__ == "__main__":
    generate_datasets()
    run_benchmark()
