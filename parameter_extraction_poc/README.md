# Aether Parameter Extraction PoC using Qwen 2.5 3B GGUF

This project is a Proof of Concept (PoC) designed to evaluate the accuracy, latency, and reliability of structured parameter extraction from natural language queries using a local offline LLM (**Qwen 2.5 3B Instruct** GGUF) and a C++ inference engine (**llama-server**).

---

## Architecture Improvements

Unlike typical Python scripts that compile heavyweight, platform-specific bindings like `llama-cpp-python` locally (which requires Ninja/CMake and is error-prone in offline environments), this PoC uses the **production-aligned sidecar architecture**:

1. **Subprocess Sidecar**: [extractor.py](file:///c:/Users/lenovo/dev/ather/JARVIS_MARK_7/parameter_extraction_poc/extractor.py) launches a precompiled [llama-server.exe](file:///C:/Users/lenovo/dev/ather/aether-main/runtime/windows-x64/llama-server.exe) sidecar.
2. **Q4_K_M Model Config & Fallback**: Configured to run `qwen2.5-3b-instruct-q4_k_m.gguf` by default, with automatic fallback to the cached `qwen2.5-3b-instruct-q2_k.gguf` model if Q4_K_M is not present on disk.
3. **JSON Schema Grammar Constraints**: Leverages `llama-server`'s grammar-constrained generation by passing `json_schema` in the request. This mathematically forces the LLM to output characters that match our JSON schemas, eliminating runaway text generation and malformed JSON.
4. **Deterministic Completion Settings**: Configured with temperature `0.0`, top_p `1.0`, max tokens `64`, and stop sequences (`["\nUser:", "\nAssistant:", "\nHuman:", "\n\n"]`).
5. **Robust Parsing Pipeline**:
   - Primary: Standard `json.loads(text)`
   - Fallback: `json-repair` (`json_repair.loads(text)`) to fix minor JSON syntax issues.
   - Final Fallback: Regex extraction of the first `{...}` JSON substring.
6. **Inference Bypass**: Skip LLM inference completely for empty schemas (`{}`) like `shutdown_system`, saving latency.

---

## Project Structure

```
parameter_extraction_poc/
│
├── config.py            # Global paths to llama-server.exe and Qwen GGUF model (with fallback)
├── prompts.py           # Contains the upgraded parameter extraction prompt template
├── schemas.py           # Tool schemas and Pydantic validation models
├── test_cases.py        # 17 ground truth test cases (kept separate for benchmark)
├── extractor.py         # Subprocess launcher, grammar-constraints and robust parsing pipeline
├── evaluate.py          # Benchmark runner that fires up the server and prints upgraded stats
├── requirements.txt     # Requirements file for execution (pydantic + requests + json-repair)
└── README.md            # System documentation and manuals
```

---

## Setup & Running

Verify that you are running inside a Python environment containing `pydantic`, `requests`, and `json-repair`.

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the evaluation suite:
   ```bash
   python evaluate.py
   ```

The script will automatically:
1. Fire up `llama-server.exe` in the background (loading Qwen 2.5 3B).
2. Wait until the server is ready.
3. Loop over the 17 queries in `test_cases.py` and run parameter extraction.
4. Calculate latency, accuracy, JSON validity, repair rate, grammar usage, and hallucination rates.
5. Print a complete, formatted terminal report.
6. Safely shut down and clean up the sidecar process.

---

## Success Criteria Targets

- **JSON Validity Rate**: $\ge 98\%$
- **Extraction Accuracy**: $\ge 90\%$
- **Average Latency**: $< 5$ seconds
- **Hallucination Rate**: $< 5\%$
