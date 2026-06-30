"""
main.py

The main CLI interactive launcher for Aether assistant.
Handles process startup/shutdown and logging hooks.
"""

import sys
import os
import logging
import time
from pathlib import Path

# Add project root to path to resolve aether packages
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aether.config import LOG_FILE
from aether.llm.model import start_server, stop_server
from aether.assistant import run_query

def setup_logging():
    """Sets up file and console log handlers."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Suppress verbose logging from external packages and indexer
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("aether.tools.indexer").setLevel(logging.WARNING)

def main():
    setup_logging()
    logger = logging.getLogger("aether_main")
    
    print("\n" + "="*60)
    print("      AETHER — OFFLINE AI DESKTOP ASSISTANT (V1)")
    print("="*60)
    print("Initializing system. Please wait...")

    # Start the sidecar server
    if not start_server():
        print("\n[Error] Failed to initialize local LLM sidecar server. Exiting.")
        sys.exit(1)

    # Start background file indexer refresh daemon
    from aether.tools.indexer import start_background_refresh
    start_background_refresh()

    print("\nSystem ready! Type your command below.")
    print("Type 'exit' or 'quit' to close the assistant.")
    print("="*60 + "\n")

    try:
        while True:
            try:
                query = input("Aether > ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nExiting...")
                break
                
            if not query:
                continue
                
            if query.lower() in ("exit", "quit"):
                print("Shutting down...")
                break

            # Execute assistant pipeline
            result = run_query(query)
            
            # Print response
            print("-" * 60)
            if result["success"]:
                print(f"Success: {result['output']}")
            else:
                print(f"Failed: {result['error']}")
            print("-" * 60)
            
            metrics = result.get("metrics")
            if metrics:
                print(f"Intent Selection: {metrics['intent_time']:.2f}s")
                print(f"Parameter Extraction: {metrics['param_time']:.2f}s ({metrics['param_source']})")
                if metrics.get("clarification") != "None":
                    print(f"Clarification: {metrics['clarification']}")
                if metrics.get("fallback") != "None":
                    print(f"Fallback Search: {metrics['fallback']}")
                print(f"Validation: {metrics['validation_time']:.2f}s")
                print(f"Execution: {metrics['execution_status']}")
                print(f"Total: {metrics['total_time']:.2f}s")
            print("-" * 60 + "\n")

    finally:
        print("Stopping local LLM sidecar server...")
        stop_server()
        print("Goodbye!")

if __name__ == "__main__":
    main()
