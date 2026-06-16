# Aether — Offline Desktop AI Assistant Demo

Aether is an offline desktop assistant prototype built with Python that manages local OS-level tasks using natural language processing, regex extraction, SQLite FTS5 database searching, and FAISS-based semantic lookup.

## Installation

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Download the English language parser model for spaCy:
   ```bash
   python -m spacy download en_core_web_sm
   ```

## Running Aether

To run the CLI application:
```bash
python main.py
```

## Example Commands to Try

Here are 10 example queries representing the range of capabilities in this demo:

1. **Open Applications (Auto-run)**:
   - `open chrome`
   - `launch notepad`
2. **Retrieve Files (Auto-run, utilizes keyword SQLite FTS5 and semantic FAISS search)**:
   - `find my resume`
   - `search for PDF files`
   - `find the presentation about DevOps`
3. **Hardware & Resource Info (Auto-run)**:
   - `check CPU usage`
   - `how much RAM is free`
4. **Volume Adjustment (Auto-run, cross-platform support)**:
   - `set volume to 50`
5. **Create Files (Confirm-required)**:
   - `create a file called notes.txt`
6. **Move Files (Confirm-required)**:
   - `move notes.txt to archive`
7. **Delete Files (Confirm-required)**:
   - `delete old_draft.txt`
