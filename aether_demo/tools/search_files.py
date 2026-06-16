import re
from typing import Optional, Literal
from tools.base import BaseTool, BaseSchema
from extraction.regex_extractor import extract_file_type
from file_index.sqlite_index import search_fts
from file_index.faiss_index import search_semantic

class SearchFilesSchema(BaseSchema):
    query: str
    file_type: Optional[str] = None

class SearchFilesTool(BaseTool):
    name = "search_files"
    description = "Searches for files in the demo folder using SQLite FTS5 and semantic FAISS search."
    example_queries = [
        "find my resume", 
        "search for PDF files", 
        "find the presentation about DevOps",
        "find the test note",
        "search for notes.txt"
    ]
    schema_class = SearchFilesSchema
    safety_level: Literal["auto", "confirm"] = "auto"

    def extract(self, query: str) -> dict:
        file_type = extract_file_type(query)
        
        # Clean the query to extract the main search keyword
        clean_q = query
        if file_type:
            # Remove file type extension keywords to avoid cluttering keyword search
            clean_q = re.sub(rf"\b{file_type}\b", "", clean_q, flags=re.IGNORECASE)
            
        # Strip common stopwords and command words
        clean_q = re.sub(r"\b(?:find|search for|search|look for|my|the|a|an|about|file|files|presentation|document|documents|sheet|spreadsheet)\b", "", clean_q, flags=re.IGNORECASE)
        clean_q = re.sub(r"\s+", " ", clean_q).strip()
        
        # If nothing could be extracted, ask a clarifying question
        if not clean_q and not file_type:
            print("I couldn't understand what files you want to search.")
            user_response = input("What keyword or file type would you like to search for? ").strip()
            if not user_response:
                raise ValueError("Search query is required.")
            # Re-run extraction on user clarification
            return self.extract(user_response)
            
        return {"query": clean_q, "file_type": file_type}

    def execute(self, params: SearchFilesSchema) -> str:
        search_query = params.query
        file_type = params.file_type
        
        # 1. Query SQLite FTS5 keyword index
        # If search_query is empty but file_type is specified, we fetch files of that type.
        results_fts = []
        if search_query or file_type:
            results_fts = search_fts(search_query, file_type)
            
        results = list(results_fts)
        
        # 2. If less than 3 results from FTS5, query semantic FAISS index
        if len(results) < 3 and search_query:
            results_semantic = search_semantic(search_query, file_type)
            # Merge and deduplicate by filename / path
            seen_paths = {r["filepath"] for r in results}
            for r in results_semantic:
                if r["filepath"] not in seen_paths:
                    results.append(r)
                    seen_paths.add(r["filepath"])
                    
        # Limit to top 3 results
        final_results = results[:3]

        if not final_results:
            crit = f"'{search_query}'" if search_query else ""
            if file_type:
                crit += f" of type {file_type.upper()}"
            return f"No files found matching {crit}."
            
        # Format results
        matching_names = [r["filename"] for r in final_results]
        crit_desc = f"'{search_query}'" if search_query else f"{file_type.upper()} files"
        if search_query and file_type:
            crit_desc = f"'{search_query}' with type {file_type.upper()}"
            
        return f"Found {len(final_results)} files matching {crit_desc}: {', '.join(matching_names)}"
