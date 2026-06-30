import os
import re
import logging
import difflib
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from functools import wraps

from aether.tools.indexer import get_db_connection, compute_relative_location, add_to_index
import aether.config as config

logger = logging.getLogger(__name__)

def handle_file_suggestions(func):
    """Decorator to catch FileNotFoundError and ValueError and return them as clean error messages."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (FileNotFoundError, ValueError) as e:
            return {
                "success": False,
                "message": str(e)
            }
    return wrapper

class FileSearchService:
    @staticmethod
    def get_user_directories() -> List[Path]:
        user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
        return [
            Path(user_profile) / "Desktop",
            Path(user_profile) / "Downloads",
            Path(user_profile) / "Documents",
            Path(user_profile) / "Pictures",
            Path(user_profile) / "Videos",
            Path(user_profile) / "Music",
            Path(os.getcwd())
        ]

    @staticmethod
    def find_all_files_on_disk(name_or_path: str, is_directory: Optional[bool] = None) -> List[Path]:
        p = Path(name_or_path)
        filename = p.name
        rel_parent = p.parent
        
        # Avoid circular import
        from aether.tools.indexer import get_indexed_paths, EXCLUDED_DIRS
        drives = get_indexed_paths()
        EXCLUDED_DIRS_LOWER = {d.lower() for d in EXCLUDED_DIRS}
        
        matches = []
        for d in drives:
            try:
                for root, dirs, files_list in os.walk(d):
                    dirs[:] = [name for name in dirs if name.lower() not in EXCLUDED_DIRS_LOWER and not name.startswith(".") and not name.startswith("$")]
                    
                    if is_directory is not False:
                        for folder_name in dirs:
                            if folder_name.lower() == filename.lower():
                                candidate = Path(root) / folder_name
                                resolved = candidate.resolve()
                                if len(rel_parent.parts) > 0:
                                    if rel_parent.name.lower() in str(resolved.parent).lower():
                                        if resolved not in matches:
                                            matches.append(resolved)
                                else:
                                    if resolved not in matches:
                                        matches.append(resolved)
                                    
                    if is_directory is not True:
                        for file_name in files_list:
                            if file_name.lower() == filename.lower():
                                candidate = Path(root) / file_name
                                resolved = candidate.resolve()
                                if len(rel_parent.parts) > 0:
                                    if rel_parent.name.lower() in str(resolved.parent).lower():
                                        if resolved not in matches:
                                            matches.append(resolved)
                                else:
                                    if resolved not in matches:
                                        matches.append(resolved)
            except Exception:
                pass
        return matches

    @staticmethod
    def resolve(name_or_path: str, is_directory: Optional[bool] = None) -> Path:
        """
        Resolves a filename or path to an absolute Path object.
        If exact match is found (or exactly 1 match), returns it.
        If multiple exact matches are found, prompts the user to select one.
        If 0 exact matches are found, searches for similar filenames and prompts the user.
        If no suggestions are found, raises FileNotFoundError.
        """
        logger.info(f"FileSearchService.resolve: query='{name_or_path}', is_directory={is_directory}")
        p = Path(name_or_path)
        if p.is_absolute() and p.exists():
            if is_directory is True and not p.is_dir():
                raise FileNotFoundError(f"Path '{name_or_path}' is not a directory.")
            if is_directory is False and not p.is_file():
                raise FileNotFoundError(f"Path '{name_or_path}' is not a file.")
            return p

        filename = p.name
        rel_parent = p.parent
        
        # 1. Search index for exact filename matches
        conn = get_db_connection()
        cursor = conn.cursor()
        query_sql = "SELECT absolute_path, relative_location, is_directory FROM indexed_files WHERE filename = ?"
        params = [filename]
        if is_directory is not None:
            query_sql += " AND is_directory = ?"
            params.append(1 if is_directory else 0)
            
        cursor.execute(query_sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        # Filter by parent folder structures if specified
        if len(rel_parent.parts) > 0:
            filtered_rows = []
            for r in rows:
                rel_loc = r["relative_location"]
                if rel_loc and (rel_parent.name in rel_loc or Path(rel_loc).is_relative_to(rel_parent)):
                    filtered_rows.append(r)
            if filtered_rows:
                rows = filtered_rows
                
        # If not found in index, check standard folders
        if not rows:
            fallback_matches = []
            for d in FileSearchService.get_user_directories():
                candidate = d / name_or_path
                if candidate.exists():
                    if is_directory is True and not candidate.is_dir():
                        continue
                    if is_directory is False and not candidate.is_file():
                        continue
                    resolved = candidate.resolve()
                    if resolved not in fallback_matches:
                        fallback_matches.append(resolved)
                        
            # If still not found, perform full disk search
            if not fallback_matches:
                logger.info(f"File '{name_or_path}' not found in index. Running full disk search...")
                fallback_matches = FileSearchService.find_all_files_on_disk(name_or_path, is_directory)
                
            for match in fallback_matches:
                try:
                    add_to_index(match)
                except Exception:
                    pass
                    
            rows = [{"absolute_path": str(m), "relative_location": compute_relative_location(m), "is_directory": 1 if m.is_dir() else 0} for m in fallback_matches]

        # 2. Handle matches
        if len(rows) == 1:
            resolved_path = Path(rows[0]["absolute_path"])
            if resolved_path.exists():
                return resolved_path

        # Determine suggestions (either multiple exact matches, or similar matches)
        suggestions = []
        if len(rows) > 1:
            for idx, r in enumerate(rows[:5], 1):
                suggestions.append({
                    "id": idx,
                    "filename": Path(r["absolute_path"]).name,
                    "path": r["absolute_path"],
                    "is_directory": bool(r["is_directory"])
                })
        else:
            # Search for similar filenames (suggestions)
            suggestions = FileSearchService.search_suggestions(name_or_path, is_directory)

        if not suggestions:
            raise FileNotFoundError(f"I couldn't find any matching files or folders for '{name_or_path}'.")

        # 3. Prompt the user using prompt_user_sync
        from aether.api.prompt import prompt_user_sync
        
        title = f"I couldn't find an exact match for \"{name_or_path}\". Did you mean:"
        options = []
        for sug in suggestions:
            emoji = "📂" if sug["is_directory"] else "📄"
            options.append(f"{emoji} {sug['filename']} ({sug['path']})")
        options.append("Cancel")

        choice = prompt_user_sync(title, options).strip()
        
        if choice.lower() in ("cancel", "abort") or choice == str(len(options)):
            raise ValueError("Operation cancelled.")

        # Resolve selection
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(suggestions):
                resolved_path = Path(suggestions[idx]["path"])
                if resolved_path.exists():
                    return resolved_path
                else:
                    raise FileNotFoundError(f"The selected file '{resolved_path}' does not exist.")
        else:
            # Check for filename match (case-insensitive)
            for sug in suggestions:
                if choice.lower() == sug["filename"].lower() or choice.lower() == sug["path"].lower():
                    resolved_path = Path(sug["path"])
                    if resolved_path.exists():
                        return resolved_path
            raise ValueError(f"Invalid selection: '{choice}'.")

    @staticmethod
    def search_suggestions(query: str, is_directory: Optional[bool] = None) -> List[Dict[str, Any]]:
        # Clean query and get filename part
        clean_query = Path(query).name
        words = [w for w in re.split(r'[\s_\-\.]+', clean_query) if w]
        if not words:
            return []
            
        conditions = []
        params = []
        for w in words:
            conditions.append("filename LIKE ?")
            params.append(f"%{w}%")
            
        sql = "SELECT filename, absolute_path, is_directory, relative_location FROM indexed_files WHERE (" + " OR ".join(conditions) + ")"
        if is_directory is not None:
            sql += " AND is_directory = ?"
            params.append(1 if is_directory else 0)
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        # Rank candidates using difflib
        candidates = []
        query_lower = clean_query.lower()
        for row in rows:
            filename = row["filename"]
            filename_lower = filename.lower()
            
            ratio = difflib.SequenceMatcher(None, query_lower, filename_lower).ratio()
            
            # Boosts
            if query_lower in filename_lower:
                ratio += 0.5
            if filename_lower.startswith(query_lower):
                ratio += 0.3
                
            candidates.append((ratio, row))
            
        # Sort by ratio descending
        candidates.sort(key=lambda x: x[0], reverse=True)
        
        # Format top 5 suggestions
        suggestions = []
        seen_paths = set()
        for ratio, row in candidates:
            abs_path = row["absolute_path"]
            if abs_path in seen_paths:
                continue
            seen_paths.add(abs_path)
            
            suggestions.append({
                "id": len(suggestions) + 1,
                "filename": row["filename"],
                "path": abs_path,
                "is_directory": bool(row["is_directory"])
            })
            if len(suggestions) >= 5:
                break
                
        return suggestions
