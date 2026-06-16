import os
import difflib
from typing import Literal
from tools.base import BaseTool, BaseSchema
from extraction.spacy_extractor import extract_filename_candidates
from config import DEMO_DIR

class DeleteFileSchema(BaseSchema):
    file_path: str

class DeleteFileTool(BaseTool):
    name = "delete_file"
    description = "Deletes a specified file from the demo folder after confirmation."
    example_queries = ["delete old_report.pdf", "remove the test file", "trash notes.txt"]
    schema_class = DeleteFileSchema
    safety_level: Literal["auto", "confirm"] = "confirm"

    def get_action_description(self, params: DeleteFileSchema) -> str:
        filename = os.path.basename(params.file_path)
        return f"Delete file '{filename}' from {DEMO_DIR}?"

    def extract(self, query: str) -> dict:
        # Create demo dir if not exists
        os.makedirs(DEMO_DIR, exist_ok=True)
        
        all_files = [f for f in os.listdir(DEMO_DIR) if os.path.isfile(os.path.join(DEMO_DIR, f))]
        candidates = extract_filename_candidates(query)
        
        matched_file = None
        
        if candidates:
            for cand in candidates:
                # 1. Exact match (case insensitive)
                for f in all_files:
                    if f.lower() == cand.lower():
                        matched_file = f
                        break
                if matched_file:
                    break
                
                # 2. Substring match
                sub_matches = [f for f in all_files if cand.lower() in f.lower()]
                if len(sub_matches) == 1:
                    matched_file = sub_matches[0]
                    break
                elif len(sub_matches) > 1:
                    print(f"Multiple files matched '{cand}':")
                    for idx, f in enumerate(sub_matches, 1):
                        print(f"  {idx}. {f}")
                    ans = input("Which file did you mean? (Enter number): ").strip()
                    if ans.isdigit() and 1 <= int(ans) <= len(sub_matches):
                        matched_file = sub_matches[int(ans) - 1]
                    else:
                        for f in sub_matches:
                            if ans.lower() in f.lower():
                                matched_file = f
                                break
                    if matched_file:
                        break
                
                # 3. Fuzzy match using close matches
                close_matches = difflib.get_close_matches(cand, all_files, n=3, cutoff=0.5)
                if len(close_matches) == 1:
                    matched_file = close_matches[0]
                    break
                elif len(close_matches) > 1:
                    print(f"Multiple potential matches found for '{cand}':")
                    for idx, f in enumerate(close_matches, 1):
                        print(f"  {idx}. {f}")
                    ans = input("Which file did you mean? (Enter number): ").strip()
                    if ans.isdigit() and 1 <= int(ans) <= len(close_matches):
                        matched_file = close_matches[int(ans) - 1]
                    else:
                        for f in close_matches:
                            if ans.lower() in f.lower():
                                matched_file = f
                                break
                    if matched_file:
                        break

        if not matched_file:
            print("I couldn't identify the file to delete.")
            ans = input("Please specify the exact filename: ").strip()
            if ans in all_files:
                matched_file = ans
            elif os.path.exists(os.path.join(DEMO_DIR, ans)):
                matched_file = ans
            else:
                raise ValueError(f"File '{ans}' does not exist in {DEMO_DIR}.")
                
        return {"file_path": os.path.join(DEMO_DIR, matched_file)}

    def execute(self, params: DeleteFileSchema) -> str:
        filepath = params.file_path
        filename = os.path.basename(filepath)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File '{filename}' does not exist.")
            
        os.remove(filepath)
        return f"Deleted {filename}."
