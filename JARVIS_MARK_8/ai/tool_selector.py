"""
ai/tool_selector.py

Implements preprocessing (typo correction, alias normalization) and tool selection
using BGE embeddings and FAISS similarity lookup.
Initializes the database index automatically if not found.
"""

import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from validation.schemas import TOOL_REGISTRY

# Paths for local offline data
AI_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(AI_DIR, "data")
MODEL_DIR = os.path.join(DATA_DIR, "model")
INDEX_PATH = os.path.join(DATA_DIR, "faiss.index")
METADATA_PATH = os.path.join(DATA_DIR, "tool_metadata.json")

# Define example queries for tool indexing
TOOL_EXAMPLES = {
    "open_app": [
        "Open Chrome", "Launch VS Code", "Start Spotify", "Open Discord",
        "Please open Notepad", "Start Chrome browser", "Open my web browser window",
        "open Notepad", "open notepad", "launch notepad", "start notepad"
    ],
    "close_app": [
        "Close Chrome", "Exit VS Code", "Terminate Spotify", "Close Discord",
        "Kill Calculator", "Stop Chrome browser", "Close the browser application",
        "close notepad", "Close Notepad", "can you close notepad for me",
        "close Chrome", "close spotify"
    ],
    "list_installed_apps": [
        "List installed applications", "What software is installed?", "Show all programs",
        "List my apps", "What apps do I have installed on this computer?"
    ],
    "set_volume": [
        "Set volume to 50%", "Change volume to 20%", "Increase sound to 70%",
        "Lower volume to 10%", "Adjust sound level to 80"
    ],
    "increase_volume": [
        "Turn up the volume", "Make it louder", "Increase sound", "Raise volume level",
        "Turn the sound up a bit", "Boost the audio output"
    ],
    "decrease_volume": [
        "Turn down the volume", "Make it quieter", "Decrease sound", "Lower volume level",
        "Turn the sound down a bit", "Reduce the audio output"
    ],
    "mute_volume": [
        "Mute sound", "Mute the volume", "Silence the audio", "Turn off system sound",
        "Silence my PC", "Mute the speakers"
    ],
    "unmute_volume": [
        "Unmute sound", "Turn sound back on", "Restore volume", "Unmute audio",
        "Enable the audio sound", "Bring back the sound"
    ],
    "set_brightness": [
        "Set brightness to 60%", "Adjust brightness to 80", "Set screen brightness to 50%",
        "Configure display brightness to 90 percent", "Adjust monitor brightness to 40%"
    ],
    "increase_brightness": [
        "Make the screen brighter", "Increase brightness", "Turn up brightness",
        "Brighten the screen", "Turn up screen brightness", "It is too dark", "It's too dark", "cannot see anything", "make screen brighter"
    ],
    "decrease_brightness": [
        "Make the screen dimmer", "Decrease brightness", "Turn down screen brightness",
        "Dim the screen", "Reduce screen light", "It's too bright", "The screen is too bright", "too bright", "make the screen less bright"
    ],
    "search_file": [
        "Find my resume", "Search for report.pdf", "Locate tax documents",
        "Where is presentation.pptx?", "Can you find notes.txt?", "Search for AI project files"
    ],
    "open_file": [
        "Open report.pdf", "Open my resume", "Launch presentation.pptx",
        "Open notes.txt", "Show me assignment.docx", "Open the tax document"
    ],
    "create_file": [
        "Create notes.txt", "Make a new file called todo.txt", "Create report.docx",
        "Generate meeting_notes.txt", "Make a text file named ideas.txt",
        "Create report.txt", "Create a new file report.txt", "make file report.txt"
    ],
    "delete_file": [
        "Delete report.pdf", "Remove notes.txt", "Delete my resume",
        "Trash assignment.docx", "Erase meeting_notes.txt"
    ],
    "rename_file": [
        "Rename report.pdf to annual_report.pdf", "Change name of resume.docx to resume_v2.docx",
        "Rename notes.txt to todo.txt", "Give a new name to data.csv"
    ],
    "move_file": [
        "Move report.pdf to Downloads", "Transfer notes.txt to Documents",
        "Move tax.pdf into Backup", "Put assignment.docx in Desktop"
    ],
    "copy_file": [
        "Copy report.pdf to Downloads", "Duplicate notes.txt in Documents",
        "Make a copy of tax.pdf in Backup", "Copy assignment.docx to the Desktop folder"
    ],
    "create_folder": [
        "Create folder AI Projects", "Make a folder called Work",
        "Generate a directory named Resume", "Create a folder for DevOps"
    ],
    "delete_folder": [
        "Delete folder AI Projects", "Remove directory Work",
        "Trash the Resume directory", "Remove the folder named test_data"
    ],
    "rename_folder": [
        "Rename folder AI Projects to Machine Learning", "Change directory name from Work to Job",
        "Rename folder Resume to CV", "Change name of directory downloads to files"
    ],
    "open_notepad_and_write": [
        "Open Notepad and write hello world", "Launch Notepad and type meeting notes",
        "Start Notepad and write hey there", "Open text editor and type shopping list"
    ],
    "append_to_file": [
        "Append hello to notes.txt", "Add this line to todo.txt",
        "Write some more text to report.txt", "Append meeting notes to notes.txt"
    ],
    "read_file_content": [
        "Read notes.txt", "Show contents of report.docx", "What is inside todo.txt?",
        "Display the text file content", "Print text contents of summary.txt"
    ],
    "take_screenshot": [
        "Take a screenshot", "Capture the screen", "Take a snapshot of the display",
        "Save a screenshot of the window"
    ],
    "shutdown_system": [
        "Shutdown the computer", "Turn off my PC", "Power off the system",
        "Shut down Windows", "Turn off the machine"
    ]
}

def preprocess_query(query: str) -> str:
    """
    Cleans up query to normalize typos and common aliases.
    """
    q = query.lower().strip()
    
    # Remove punctuation
    for char in [".", ",", "!", "?", "'", '"', "(", ")", ";", ":"]:
        q = q.replace(char, "")
        
    # Typo correction
    typos = {
        "opne": "open",
        "chorme": "chrome",
        "spotfiy": "spotify",
        "notpad": "notepad",
        "brwoser": "browser",
        "reboot": "restart",
        "shut down": "shutdown"
    }
    words = q.split()
    corrected_words = [typos.get(w, w) for w in words]
    q = " ".join(corrected_words)
    
    # Aliases
    aliases = {
        "google chrome browser": "Chrome",
        "google chrome": "Chrome",
        "chrome browser": "Chrome",
        "visual studio code": "VS Code",
        "vscode": "VS Code",
        "browser": "Chrome"
    }
    for alias, replacement in aliases.items():
        if alias in q:
            q = q.replace(alias, replacement)
            
    return q

class ToolSelector:
    def __init__(self, threshold: float = 0.65):
        self.threshold = threshold
        self.model = None
        self.index = None
        self.metadata = []
        
        # Initialize resources
        self._initialize_resources()
        
    def _initialize_resources(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Load local model or download first
        if os.path.exists(MODEL_DIR):
            print("[Selector] Loading SentenceTransformer locally...")
            self.model = SentenceTransformer(MODEL_DIR, local_files_only=True)
        else:
            print("[Selector] Local model not found. Downloading BAAI/bge-small-en-v1.5 from Hugging Face...")
            self.model = SentenceTransformer("BAAI/bge-small-en-v1.5")
            print(f"[Selector] Saving model to local cache: {MODEL_DIR}")
            self.model.save(MODEL_DIR)
            
        # Rebuild index on every initialization to dynamic updates
        self.build_index()
            
        # Load FAISS index and metadata
        self.index = faiss.read_index(INDEX_PATH)
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)
            
    def build_index(self):
        """
        Creates and saves a new FAISS index based on tool examples.
        """
        print("[Selector] Building FAISS similarity index...")
        documents = []
        metadata = []
        
        for tool_name, examples in TOOL_EXAMPLES.items():
            desc = TOOL_REGISTRY[tool_name]["description"]
            # Add description document
            doc_desc = f"Tool: {tool_name}\nDescription: {desc}"
            documents.append(doc_desc)
            metadata.append(tool_name)
            
            # Add example documents
            for ex in examples:
                doc_ex = f"Tool: {tool_name}\nExample: {ex}"
                documents.append(doc_ex)
                metadata.append(tool_name)
                
        # Generate embeddings
        embeddings = self.model.encode(documents, show_progress_bar=False)
        embeddings = np.array(embeddings).astype("float32")
        
        # L2 normalize for Inner Product (Cosine Similarity)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1e-10, norms)
        normalized_embeddings = embeddings / norms
        
        dimension = normalized_embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)
        index.add(normalized_embeddings)
        
        # Persist index and metadata mapping
        faiss.write_index(index, INDEX_PATH)
        with open(METADATA_PATH, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
        print(f"[Selector] Saved FAISS index with {len(documents)} entries.")
        
    def select_tool(self, query: str) -> dict:
        """
        Preprocesses query and performs cosine similarity matching.
        """
        preprocessed = preprocess_query(query)
        
        # Format query for BGE asymmetric search
        query_text = f"Represent this sentence for searching relevant passages: {preprocessed}"
        
        # Generate embedding
        q_emb = self.model.encode([query_text])
        q_emb = np.array(q_emb).astype("float32")
        
        # L2-normalize query
        q_norm = np.linalg.norm(q_emb, axis=1, keepdims=True)
        q_norm = np.where(q_norm == 0, 1e-10, q_norm)
        q_emb_normalized = q_emb / q_norm
        
        # Query index for top 3
        scores, indices = self.index.search(q_emb_normalized, 3)
        
        top_matches = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1:
                tool_name = self.metadata[idx]
                top_matches.append({
                    "tool": tool_name,
                    "score": float(score)
                })
                
        # Group matches to select the highest scoring unique tool
        unique_matches = {}
        for match in top_matches:
            tool = match["tool"]
            score = match["score"]
            if tool not in unique_matches or score > unique_matches[tool]:
                unique_matches[tool] = score
                
        sorted_matches = sorted(
            [{"tool": t, "score": s} for t, s in unique_matches.items()],
            key=lambda x: x["score"],
            reverse=True
        )
        
        if not sorted_matches:
            return {"selected_tool": None, "score": 0.0, "top_matches": []}
            
        best_match = sorted_matches[0]
        selected_tool = best_match["tool"]
        score = best_match["score"]
        
        # Enforce threshold check
        if score < self.threshold:
            print(f"[Selector] Query score {score:.4f} is below threshold {self.threshold:.4f}.")
            return {
                "selected_tool": None,
                "score": score,
                "top_matches": sorted_matches,
                "requires_clarification": True
            }
            
        return {
            "selected_tool": selected_tool,
            "score": score,
            "top_matches": sorted_matches,
            "requires_clarification": False
        }
