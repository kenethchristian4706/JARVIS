# Aether Offline Tool Selection System - Proof of Concept (PoC)

This project is a Proof of Concept (PoC) designed to evaluate the accuracy and speed of identifying system tools from natural language queries using **BGE Small (`BAAI/bge-small-en-v1.5`)** embeddings and **FAISS** similarity search. It is built to run 100% offline.

---

## Features

- **完全离线 (100% Offline)**: The index generation script caches the Hugging Face model locally in `data/model/`, enabling all subsequent tool selection calls to execute without internet access.
- **BGE-Small Embeddings**: Utilizes the highly-optimized `BAAI/bge-small-en-v1.5` sentence-transformer.
- **FAISS Integration**: Uses `faiss.IndexFlatIP` combined with normalized embeddings to perform cosine similarity search in sub-millisecond times.
- **Standardized Asymmetric Search**: Implements the BGE asymmetric query instruction prefix (`Represent this sentence for searching relevant passages: `) on user queries for optimal retrieval quality.
- **56 Phase-1 Tools Supported**: Covers system control, file and folder management, clipboard operations, web searches, screen capturing, and page interaction.

---

## Project Structure

```
tool_selection_poc/
│
├── tools.py             # Defines the list of 56 tools with descriptions and examples
├── build_index.py       # Downloads the model, generates embeddings, and saves index files
├── selector.py          # Exposes the select_tool(query) API for tool matching
├── evaluate.py          # Benchmark runner checking selector against test dataset
├── test_queries.py      # Ground truth evaluation queries (kept separate from indexing)
├── requirements.txt     # Project package dependencies
├── data/                # Created by build_index.py (git ignored in production)
│   ├── model/           # Locally cached SentenceTransformer model files
│   ├── faiss.index      # Saved FAISS index database file
│   └── tool_metadata.json # List of tool names mapping indices to tools
└── README.md            # System documentation and guides
```

---

## Prerequisites & Installation

Verify that you have Python 3.8+ installed.

Install the required packages using pip:

```bash
pip install -r requirements.txt
```

---

## How to Run

### Step 1: Build the Offline Index

Run the build script to download the model from Hugging Face, format the tool documents, generate embeddings, and save the search database locally:

```bash
python build_index.py
```

*This script requires an internet connection during its first run to download `BAAI/bge-small-en-v1.5` (approx. 90MB). All subsequent steps can run completely offline.*

### Step 2: Run the Accuracy Benchmark

Run the evaluation script to test the selector against the 23 queries inside `test_queries.py`:

```bash
python evaluate.py
```

The script will print out:
- Total accuracy (target is >= 85%, goal is 90-95%+)
- Average similarity scores for successful and failed matches
- A list of any failed predictions
- A clean, filtered ASCII confusion matrix mapping active labels

---

## API Usage

You can import and use the tool selector in your own desktop assistant scripts:

```python
from selector import select_tool

# Example query
result = select_tool("Please increase the sound to 70%")

print(result)
# Output:
# {
#     "selected_tool": "set_volume",
#     "score": 0.9123,
#     "top_matches": [
#         {"tool": "set_volume", "score": 0.9123},
#         {"tool": "increase_volume", "score": 0.7654},
#         {"tool": "decrease_volume", "score": 0.5432}
#     ]
# }
```

---

## Optimization Details

### Document Format
Each tool is indexed as a structured text block:
```
Tool: <tool_name>

Description:
<description>

Examples:
- example_1
- example_2
```

### Retrieval Prompting
BGE models are trained asymmetrically. To query documents using short queries, we prepend:
`Represent this sentence for searching relevant passages: ` to the query embedding process, while keeping indexed document representations instruction-free.

### Similarity Calculation
FAISS is configured to use inner product (`IndexFlatIP`). By L2-normalizing the vectors before adding them to the index and normalizing the query vector before searching, the inner product calculation corresponds exactly to the cosine similarity.
