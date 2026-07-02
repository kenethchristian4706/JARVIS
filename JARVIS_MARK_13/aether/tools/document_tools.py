"""
tools/document_tools.py

Implements tool wrappers for Word and Excel document creation, reading, and editing.
Conforms to Aether's tool registry format.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Any

from aether.tools.file_tools import resolve_path, resolve_filename
from aether.documents.common.word import create_word_doc, read_word_doc, edit_word_doc
from aether.documents.common.excel import create_excel_workbook, read_excel_workbook, write_excel_cell
from aether.documents.common.exceptions import DocumentError

logger = logging.getLogger(__name__)

def create_word(
    filename: str,
    directory: Optional[str] = None,
    content: Optional[str] = None,
    overwrite: bool = False
) -> dict:
    """
    Creates a new Microsoft Word document (.docx).
    """
    try:
        logger.info(f"Tool create_word: filename='{filename}', directory='{directory}', overwrite={overwrite}")
        
        # Ensure .docx extension is appended if missing
        if not filename.lower().endswith(".docx"):
            filename += ".docx"
            
        file_path = None
        prompted_for_location = False
        
        # 1. FIRST check if file exists in database (if no directory was specified)
        if not directory and not overwrite:
            from aether.tools.indexer import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT absolute_path FROM indexed_files WHERE filename = ? AND is_directory = 0", (filename,))
            rows = cursor.fetchall()
            conn.close()
            
            if rows:
                from aether.api.prompt import prompt_user_sync
                title = f"A file named '{filename}' already exists. What would you like to do?"
                options = ["Choose Existing File", "Create Another", "Cancel"]
                choice = prompt_user_sync(title, options).strip()
                
                if choice == '1' or choice.lower().startswith("choose") or choice.lower().startswith("open"):
                    if len(rows) == 1:
                        file_path = Path(rows[0][0])
                    else:
                        title_select = f"Which '{filename}' file would you like to choose?"
                        select_options = [r[0] for r in rows]
                        select_choice = prompt_user_sync(title_select, select_options).strip()
                        if select_choice.isdigit():
                            idx = int(select_choice) - 1
                            if 0 <= idx < len(rows):
                                file_path = Path(rows[idx][0])
                            else:
                                raise ValueError("Invalid selection.")
                        else:
                            found = False
                            for r in rows:
                                if select_choice.lower() == r[0].lower():
                                    file_path = Path(r[0])
                                    found = True
                                    break
                            if not found:
                                raise ValueError("Invalid selection.")
                    return {
                        "success": True,
                        "message": f"Successfully selected existing file at '{file_path}' (No changes made).",
                        "data": {
                            "path": str(file_path.resolve()),
                            "filename": file_path.name
                        }
                    }
                elif choice == '2' or choice.lower().startswith("create"):
                    from aether.api.prompt import prompt_user_sync
                    from aether.platforms.common.paths import PlatformPaths
                    
                    title_loc = f"Where would you like to create the document '{filename}'?"
                    options_loc = ["Desktop", "Downloads", "Documents", "Current Working Directory", "Custom Path"]
                    choice_loc = prompt_user_sync(title_loc, options_loc).strip()
                    
                    if choice_loc == "1" or choice_loc.lower() == "desktop":
                        target_dir = PlatformPaths.get_desktop()
                    elif choice_loc == "2" or choice_loc.lower() == "downloads":
                        target_dir = PlatformPaths.get_downloads()
                    elif choice_loc == "3" or choice_loc.lower() == "documents":
                        target_dir = PlatformPaths.get_documents()
                    elif choice_loc == "4" or choice_loc.lower().startswith("current"):
                        target_dir = Path(os.getcwd())
                    elif choice_loc == "5" or choice_loc.lower().startswith("custom"):
                        custom_path = prompt_user_sync("Enter custom directory path:", []).strip()
                        if not custom_path:
                            raise ValueError("Custom path is required.")
                        target_dir = resolve_path(custom_path)
                    else:
                        target_dir = resolve_path(choice_loc) if choice_loc else Path(os.getcwd())
                    
                    file_path = target_dir / filename
                    prompted_for_location = True
                else:
                    raise ValueError("Operation cancelled by user.")

        # If not resolved yet (was not in database or directory was supplied initially)
        if not file_path:
            if directory:
                target_dir = resolve_path(directory)
                file_path = target_dir / filename
            else:
                if "/" in filename or "\\" in filename or filename.startswith("~"):
                    file_path = resolve_path(filename)
                else:
                    if not prompted_for_location:
                        from aether.api.prompt import prompt_user_sync
                        from aether.platforms.common.paths import PlatformPaths
                        
                        title_loc = f"Where would you like to create the document '{filename}'?"
                        options_loc = ["Desktop", "Downloads", "Documents", "Current Working Directory", "Custom Path"]
                        choice_loc = prompt_user_sync(title_loc, options_loc).strip()
                        
                        if choice_loc == "1" or choice_loc.lower() == "desktop":
                            target_dir = PlatformPaths.get_desktop()
                        elif choice_loc == "2" or choice_loc.lower() == "downloads":
                            target_dir = PlatformPaths.get_downloads()
                        elif choice_loc == "3" or choice_loc.lower() == "documents":
                            target_dir = PlatformPaths.get_documents()
                        elif choice_loc == "4" or choice_loc.lower().startswith("current"):
                            target_dir = Path(os.getcwd())
                        elif choice_loc == "5" or choice_loc.lower().startswith("custom"):
                            custom_path = prompt_user_sync("Enter custom directory path:", []).strip()
                            if not custom_path:
                                raise ValueError("Custom path is required.")
                            target_dir = resolve_path(custom_path)
                        else:
                            target_dir = resolve_path(choice_loc) if choice_loc else Path(os.getcwd())
                    else:
                        target_dir = Path(os.getcwd())
                    file_path = target_dir / filename
                    
        path_str = create_word_doc(file_path, content, overwrite)
        
        # Add created file to index
        try:
            from aether.tools.indexer import add_to_index
            add_to_index(Path(path_str))
        except Exception as idx_err:
            logger.warning(f"Failed to add new Word document to search index: {idx_err}")
        
        return {
            "success": True,
            "message": f"Word document '{filename}' created successfully.",
            "data": {
                "path": path_str,
                "filename": Path(path_str).name
            }
        }
    except Exception as e:
        logger.error(f"Error in create_word tool: {e}")
        return {
            "success": False,
            "message": f"Failed to create Word document: {str(e)}"
        }

def read_word(file_path: str) -> dict:
    """
    Reads paragraphs from a Microsoft Word document (.docx).
    """
    try:
        logger.info(f"Tool read_word: file_path='{file_path}'")
        resolved = resolve_filename(file_path, is_directory=False)
        
        if not resolved.name.lower().endswith(".docx"):
            return {
                "success": False,
                "message": "Unsupported file extension. Only .docx files are supported."
            }
            
        content = read_word_doc(resolved)
        return {
            "success": True,
            "message": "Successfully read Word document.",
            "data": {
                "content": content
            }
        }
    except Exception as e:
        logger.error(f"Error in read_word tool: {e}")
        return {
            "success": False,
            "message": f"Failed to read Word document: {str(e)}"
        }

def edit_word(
    file_path: str,
    operation: str,
    text: Optional[str] = None,
    old_text: Optional[str] = None,
    new_text: Optional[str] = None
) -> dict:
    """
    Modifies an existing Microsoft Word document (.docx).
    """
    try:
        logger.info(f"Tool edit_word: file_path='{file_path}', operation='{operation}'")
        resolved = resolve_filename(file_path, is_directory=False)
        
        if not resolved.name.lower().endswith(".docx"):
            return {
                "success": False,
                "message": "Unsupported file extension. Only .docx files are supported."
            }
            
        message = edit_word_doc(resolved, operation, text, old_text, new_text)
        return {
            "success": True,
            "message": message,
            "data": {
                "path": str(resolved.resolve())
            }
        }
    except Exception as e:
        logger.error(f"Error in edit_word tool: {e}")
        return {
            "success": False,
            "message": f"Failed to edit Word document: {str(e)}"
        }

def create_excel(
    filename: str,
    directory: Optional[str] = None,
    sheet_name: Optional[str] = None,
    overwrite: bool = False
) -> dict:
    """
    Creates a new Excel workbook (.xlsx).
    """
    try:
        logger.info(f"Tool create_excel: filename='{filename}', directory='{directory}', overwrite={overwrite}")
        
        if not filename.lower().endswith(".xlsx"):
            filename += ".xlsx"
            
        file_path = None
        prompted_for_location = False
        
        # 1. FIRST check if file exists in database (if no directory was specified)
        if not directory and not overwrite:
            from aether.tools.indexer import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT absolute_path FROM indexed_files WHERE filename = ? AND is_directory = 0", (filename,))
            rows = cursor.fetchall()
            conn.close()
            
            if rows:
                from aether.api.prompt import prompt_user_sync
                title = f"A file named '{filename}' already exists. What would you like to do?"
                options = ["Choose Existing File", "Create Another", "Cancel"]
                choice = prompt_user_sync(title, options).strip()
                
                if choice == '1' or choice.lower().startswith("choose") or choice.lower().startswith("open"):
                    if len(rows) == 1:
                        file_path = Path(rows[0][0])
                    else:
                        title_select = f"Which '{filename}' file would you like to choose?"
                        select_options = [r[0] for r in rows]
                        select_choice = prompt_user_sync(title_select, select_options).strip()
                        if select_choice.isdigit():
                            idx = int(select_choice) - 1
                            if 0 <= idx < len(rows):
                                file_path = Path(rows[idx][0])
                            else:
                                raise ValueError("Invalid selection.")
                        else:
                            found = False
                            for r in rows:
                                if select_choice.lower() == r[0].lower():
                                    file_path = Path(r[0])
                                    found = True
                                    break
                            if not found:
                                raise ValueError("Invalid selection.")
                    return {
                        "success": True,
                        "message": f"Successfully selected existing file at '{file_path}' (No changes made).",
                        "data": {
                            "path": str(file_path.resolve()),
                            "filename": file_path.name
                        }
                    }
                elif choice == '2' or choice.lower().startswith("create"):
                    from aether.api.prompt import prompt_user_sync
                    from aether.platforms.common.paths import PlatformPaths
                    
                    title_loc = f"Where would you like to create the workbook '{filename}'?"
                    options_loc = ["Desktop", "Downloads", "Documents", "Current Working Directory", "Custom Path"]
                    choice_loc = prompt_user_sync(title_loc, options_loc).strip()
                    
                    if choice_loc == "1" or choice_loc.lower() == "desktop":
                        target_dir = PlatformPaths.get_desktop()
                    elif choice_loc == "2" or choice_loc.lower() == "downloads":
                        target_dir = PlatformPaths.get_downloads()
                    elif choice_loc == "3" or choice_loc.lower() == "documents":
                        target_dir = PlatformPaths.get_documents()
                    elif choice_loc == "4" or choice_loc.lower().startswith("current"):
                        target_dir = Path(os.getcwd())
                    elif choice_loc == "5" or choice_loc.lower().startswith("custom"):
                        custom_path = prompt_user_sync("Enter custom directory path:", []).strip()
                        if not custom_path:
                            raise ValueError("Custom path is required.")
                        target_dir = resolve_path(custom_path)
                    else:
                        target_dir = resolve_path(choice_loc) if choice_loc else Path(os.getcwd())
                    
                    file_path = target_dir / filename
                    prompted_for_location = True
                else:
                    raise ValueError("Operation cancelled by user.")

        # If not resolved yet (was not in database or directory was supplied initially)
        if not file_path:
            if directory:
                target_dir = resolve_path(directory)
                file_path = target_dir / filename
            else:
                if "/" in filename or "\\" in filename or filename.startswith("~"):
                    file_path = resolve_path(filename)
                else:
                    if not prompted_for_location:
                        from aether.api.prompt import prompt_user_sync
                        from aether.platforms.common.paths import PlatformPaths
                        
                        title_loc = f"Where would you like to create the workbook '{filename}'?"
                        options_loc = ["Desktop", "Downloads", "Documents", "Current Working Directory", "Custom Path"]
                        choice_loc = prompt_user_sync(title_loc, options_loc).strip()
                        
                        if choice_loc == "1" or choice_loc.lower() == "desktop":
                            target_dir = PlatformPaths.get_desktop()
                        elif choice_loc == "2" or choice_loc.lower() == "downloads":
                            target_dir = PlatformPaths.get_downloads()
                        elif choice_loc == "3" or choice_loc.lower() == "documents":
                            target_dir = PlatformPaths.get_documents()
                        elif choice_loc == "4" or choice_loc.lower().startswith("current"):
                            target_dir = Path(os.getcwd())
                        elif choice_loc == "5" or choice_loc.lower().startswith("custom"):
                            custom_path = prompt_user_sync("Enter custom directory path:", []).strip()
                            if not custom_path:
                                raise ValueError("Custom path is required.")
                            target_dir = resolve_path(custom_path)
                        else:
                            target_dir = resolve_path(choice_loc) if choice_loc else Path(os.getcwd())
                    else:
                        target_dir = Path(os.getcwd())
                    file_path = target_dir / filename
                    
        path_str = create_excel_workbook(file_path, sheet_name, overwrite)
        
        # Add created file to index
        try:
            from aether.tools.indexer import add_to_index
            add_to_index(Path(path_str))
        except Exception as idx_err:
            logger.warning(f"Failed to add new Excel workbook to search index: {idx_err}")
            
        return {
            "success": True,
            "message": f"Excel workbook '{filename}' created successfully.",
            "data": {
                "path": path_str,
                "filename": Path(path_str).name
            }
        }
    except Exception as e:
        logger.error(f"Error in create_excel tool: {e}")
        return {
            "success": False,
            "message": f"Failed to create Excel workbook: {str(e)}"
        }

def read_excel(
    file_path: str,
    sheet_name: Optional[str] = None,
    cell_range: Optional[str] = None
) -> dict:
    """
    Reads worksheet contents from an Excel workbook (.xlsx).
    """
    try:
        logger.info(f"Tool read_excel: file_path='{file_path}', sheet_name='{sheet_name}', cell_range='{cell_range}'")
        resolved = resolve_filename(file_path, is_directory=False)
        
        if not resolved.name.lower().endswith(".xlsx"):
            return {
                "success": False,
                "message": "Unsupported file extension. Only .xlsx files are supported."
            }
            
        data = read_excel_workbook(resolved, sheet_name, cell_range)
        return {
            "success": True,
            "message": "Successfully read Excel workbook.",
            "data": {
                "cells": data
            }
        }
    except Exception as e:
        logger.error(f"Error in read_excel tool: {e}")
        return {
            "success": False,
            "message": f"Failed to read Excel workbook: {str(e)}"
        }

def write_excel(
    file_path: str,
    sheet_name: str,
    cell: str,
    value: Any
) -> dict:
    """
    Writes a value to a cell in an Excel workbook (.xlsx).
    """
    try:
        logger.info(f"Tool write_excel: file_path='{file_path}', sheet_name='{sheet_name}', cell='{cell}', value='{value}'")
        resolved = resolve_filename(file_path, is_directory=False)
        
        if not resolved.name.lower().endswith(".xlsx"):
            return {
                "success": False,
                "message": "Unsupported file extension. Only .xlsx files are supported."
            }
            
        message = write_excel_cell(resolved, sheet_name, cell, value)
        return {
            "success": True,
            "message": message,
            "data": {
                "path": str(resolved.resolve())
            }
        }
    except Exception as e:
        logger.error(f"Error in write_excel tool: {e}")
        return {
            "success": False,
            "message": f"Failed to write cell in Excel workbook: {str(e)}"
        }
