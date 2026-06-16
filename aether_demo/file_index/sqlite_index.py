import os
import re
import sqlite3
from typing import List, Dict
from config import DB_PATH, DEMO_DIR

def get_db_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    # Enable FTS5 by default (standard in Python 3's sqlite3)
    return conn

def init_db():
    """Initializes the database schema with an FTS5 virtual table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Create virtual table using FTS5
    # Standard columns: filepath, filename, content
    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(
        filepath,
        filename,
        content
    );
    """)
    conn.commit()
    conn.close()

def index_file(filepath: str):
    """Indexes a single file (inserts or updates it in the FTS5 table)."""
    if not os.path.exists(filepath):
        return
        
    filename = os.path.basename(filepath)
    content = ""
    
    # Read text content for text-based files
    _, ext = os.path.splitext(filename)
    if ext.lower() in (".txt", ".md", ".json", ".xml", ".html", ".csv"):
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            pass
            
    conn = get_db_connection()
    cursor = conn.cursor()
    # FTS5 does not have standard unique constraints, so delete existing path first
    cursor.execute("DELETE FROM files_fts WHERE filepath = ?", (filepath,))
    cursor.execute(
        "INSERT INTO files_fts (filepath, filename, content) VALUES (?, ?, ?)",
        (filepath, filename, content)
    )
    conn.commit()
    conn.close()

def remove_file_from_index(filepath: str):
    """Removes a file from the index."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM files_fts WHERE filepath = ?", (filepath,))
    conn.commit()
    conn.close()

def reindex_all():
    """Wipes the FTS5 index and indexes all files in DEMO_DIR."""
    init_db()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM files_fts")
    
    if os.path.exists(DEMO_DIR):
        for root, _, files in os.walk(DEMO_DIR):
            for file in files:
                filepath = os.path.join(root, file)
                filename = file
                content = ""
                
                _, ext = os.path.splitext(filename)
                if ext.lower() in (".txt", ".md", ".json", ".xml", ".html", ".csv"):
                    try:
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                    except Exception:
                        pass
                
                cursor.execute(
                    "INSERT INTO files_fts (filepath, filename, content) VALUES (?, ?, ?)",
                    (filepath, filename, content)
                )
                
    conn.commit()
    conn.close()

def search_fts(query_str: str, file_type: str = None) -> List[Dict[str, str]]:
    """Searches the FTS5 virtual table for files matching the query and/or file type."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    results = []
    
    try:
        if not query_str:
            # If query is empty but file_type is specified, return all files (filtered below)
            cursor.execute("SELECT filepath, filename FROM files_fts")
            rows = cursor.fetchall()
        else:
            # Clean search query (escape/remove FTS5 punctuation to avoid syntax errors)
            clean_q = re.sub(r'[^\w\s]', ' ', query_str).strip()
            # If cleaning leaves it empty, do a wildcard or exact search
            if not clean_q:
                clean_q = query_str
            
            # Simple keyword search on FTS5 columns
            cursor.execute("SELECT filepath, filename FROM files_fts WHERE files_fts MATCH ?", (clean_q,))
            rows = cursor.fetchall()
            
        for row in rows:
            filepath, filename = row[0], row[1]
            # Verify file actually still exists physically
            if not os.path.exists(filepath):
                continue
                
            # Filter by file type if specified
            if file_type:
                _, ext = os.path.splitext(filename)
                if ext.lower().lstrip(".") != file_type.lower().lstrip("."):
                    continue
                    
            results.append({
                "filepath": filepath,
                "filename": filename
            })
    except sqlite3.OperationalError as e:
        # FTS5 search parsing error, fallback to substring query on database
        # This prevents crashes on queries like "?" or "*"
        like_query = f"%{query_str}%"
        cursor.execute("SELECT filepath, filename FROM files_fts WHERE filename LIKE ? OR content LIKE ?", (like_query, like_query))
        rows = cursor.fetchall()
        for row in rows:
            filepath, filename = row[0], row[1]
            if os.path.exists(filepath):
                if file_type:
                    _, ext = os.path.splitext(filename)
                    if ext.lower().lstrip(".") != file_type.lower().lstrip("."):
                        continue
                results.append({
                    "filepath": filepath,
                    "filename": filename
                })
    finally:
        conn.close()
        
    return results
