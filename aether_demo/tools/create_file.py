import os
from typing import Optional, Literal
from tools.base import BaseTool, BaseSchema
from extraction.spacy_extractor import extract_create_file_params
from config import DEMO_DIR

class CreateFileSchema(BaseSchema):
    filename: str
    content: Optional[str] = None

class CreateFileTool(BaseTool):
    name = "create_file"
    description = "Creates a new file in the demo folder with optional content."
    example_queries = ["create a file called notes.txt", "make a new text file named todo", "create meeting_notes.md"]
    schema_class = CreateFileSchema
    safety_level: Literal["auto", "confirm"] = "confirm"

    def get_action_description(self, params: CreateFileSchema) -> str:
        filename = params.filename
        if "." not in filename:
            filename += ".txt"
        desc = f"Create file '{filename}' in {DEMO_DIR}"
        if params.content:
            desc += f" with content: \"{params.content[:30]}...\""
        desc += "?"
        return desc

    def extract(self, query: str) -> dict:
        filename, content = extract_create_file_params(query)
        
        if not filename:
            # Ambiguity handling: Ask one clarifying question
            print("I couldn't extract the filename for the new file.")
            filename = input("What should be the name of the file? ").strip()
            if not filename:
                raise ValueError("Filename is required to create a file.")
                
        return {"filename": filename, "content": content}

    def execute(self, params: CreateFileSchema) -> str:
        os.makedirs(DEMO_DIR, exist_ok=True)
        
        filename = params.filename
        if "." not in filename:
            filename += ".txt"
            
        filepath = os.path.join(DEMO_DIR, filename)
        content = params.content or ""
        
        # Write to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            
        return f"Created {filename} in AetherDemo."
