import os
import shutil
import difflib
from typing import Literal
from tools.base import BaseTool, BaseSchema
from extraction.spacy_extractor import extract_move_targets
from config import DEMO_DIR

class MoveFileSchema(BaseSchema):
    source: str
    destination: str

class MoveFileTool(BaseTool):
    name = "move_file"
    description = "Moves a file to a new destination folder inside the demo directory."
    example_queries = ["move report.pdf to documents", "move notes.txt to the archive folder"]
    schema_class = MoveFileSchema
    safety_level: Literal["auto", "confirm"] = "confirm"

    def get_action_description(self, params: MoveFileSchema) -> str:
        src_name = os.path.basename(params.source)
        dest_name = os.path.basename(params.destination) or params.destination
        return f"Move '{src_name}' to subdirectory '{dest_name}'?"

    def extract(self, query: str) -> dict:
        os.makedirs(DEMO_DIR, exist_ok=True)
        all_files = [f for f in os.listdir(DEMO_DIR) if os.path.isfile(os.path.join(DEMO_DIR, f))]
        
        source_raw, dest_raw = extract_move_targets(query)
        
        # 1. Resolve source file
        matched_source = None
        if source_raw:
            # Try exact match
            for f in all_files:
                if f.lower() == source_raw.lower():
                    matched_source = f
                    break
            
            # Substring match
            if not matched_source:
                sub_matches = [f for f in all_files if source_raw.lower() in f.lower()]
                if len(sub_matches) == 1:
                    matched_source = sub_matches[0]
                elif len(sub_matches) > 1:
                    print(f"Multiple source files matched '{source_raw}':")
                    for idx, f in enumerate(sub_matches, 1):
                        print(f"  {idx}. {f}")
                    ans = input("Which source file did you mean? (Enter number): ").strip()
                    if ans.isdigit() and 1 <= int(ans) <= len(sub_matches):
                        matched_source = sub_matches[int(ans) - 1]
            
            # Fuzzy match
            if not matched_source:
                close_matches = difflib.get_close_matches(source_raw, all_files, n=3, cutoff=0.5)
                if len(close_matches) == 1:
                    matched_source = close_matches[0]
                elif len(close_matches) > 1:
                    print(f"Multiple source file candidates for '{source_raw}':")
                    for idx, f in enumerate(close_matches, 1):
                        print(f"  {idx}. {f}")
                    ans = input("Which source file did you mean? (Enter number): ").strip()
                    if ans.isdigit() and 1 <= int(ans) <= len(close_matches):
                        matched_source = close_matches[int(ans) - 1]

        # Clarification if source is missing or not resolved
        if not matched_source:
            print("I could not identify the source file to move.")
            ans = input("Please specify the exact filename of the source: ").strip()
            if ans in all_files:
                matched_source = ans
            elif os.path.exists(os.path.join(DEMO_DIR, ans)):
                matched_source = ans
            else:
                raise ValueError(f"Source file '{ans}' does not exist.")
                
        # 2. Resolve destination folder
        if not dest_raw:
            print("I could not identify the destination folder.")
            dest_raw = input("Please specify the destination directory (e.g. documents, archive): ").strip()
            if not dest_raw:
                raise ValueError("Destination is required.")
                
        # Clean destination name
        dest_clean = dest_raw.strip().strip("'\"").strip()
        # If destination is a single word or relative directory, put it inside DEMO_DIR
        if not os.path.isabs(dest_clean):
            destination_dir = os.path.join(DEMO_DIR, dest_clean)
        else:
            destination_dir = dest_clean
            
        return {
            "source": os.path.join(DEMO_DIR, matched_source),
            "destination": destination_dir
        }

    def execute(self, params: MoveFileSchema) -> str:
        src = params.source
        dest = params.destination
        
        if not os.path.exists(src):
            raise FileNotFoundError(f"Source file '{os.path.basename(src)}' does not exist.")
            
        # Ensure destination directory exists
        os.makedirs(dest, exist_ok=True)
        
        dest_file_path = os.path.join(dest, os.path.basename(src))
        shutil.move(src, dest_file_path)
        
        # Output format matching: "Moved invoice_april.pdf → AetherDemo/archive/"
        # Let's get relative destination for nicer output
        rel_dest = os.path.relpath(dest, os.path.dirname(DEMO_DIR))
        # Wait, the example: "Moved invoice_april.pdf → AetherDemo/archive/"
        # We can format it as "Moved {filename} → AetherDemo/{destination_folder_name}" or relative path
        rel_dest_nice = os.path.relpath(dest_file_path, os.path.dirname(DEMO_DIR)).replace("\\", "/")
        # If relative path starts with AetherDemo, or just use AetherDemo/archive
        if not rel_dest_nice.startswith("AetherDemo"):
            # If path points to desktop or has AetherDemo, display it cleanly
            rel_dest_nice = f"AetherDemo/{os.path.basename(dest)}"
            
        return f"Moved {os.path.basename(src)} → {rel_dest_nice}"
