"""
platform/mac/file_tools.py

macOS implementation of FileAPI.
"""

import os
import shutil
import logging
import zipfile
import subprocess
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import send2trash
import pytesseract
from PIL import Image

from aether.platforms.common.interfaces import FileAPI
from aether.platforms.common.paths import PlatformPaths
from aether.platforms.common.exceptions import AetherPlatformError
from aether.tools.indexer import add_to_index, remove_from_index, get_db_connection
from aether.tools.file_search_service import FileSearchService

logger = logging.getLogger(__name__)

# Configure pytesseract Mac Brew path
TESSERACT_CMD_CANDIDATES = [
    "/opt/homebrew/bin/tesseract",
    "/usr/local/bin/tesseract"
]
for candidate in TESSERACT_CMD_CANDIDATES:
    if os.path.exists(candidate):
        pytesseract.pytesseract.tesseract_cmd = candidate
        break

class MacFileAPI(FileAPI):
    def get_indexed_paths(self) -> List[Path]:
        paths = [Path.home()]
        volumes = Path("/Volumes")
        if volumes.exists():
            try:
                for item in volumes.iterdir():
                    if item.is_dir() and not item.is_symlink():
                        paths.append(item)
            except Exception as e:
                logger.warning(f"Error scanning volumes: {e}")
        return paths

    def resolve_path(self, target_path: str) -> Path:
        path = Path(target_path)
        if path.is_absolute():
            return path
        resolved = path.resolve()
        if resolved.exists():
            return resolved
        for parent_dir in PlatformPaths.get_user_directories():
            candidate = parent_dir / target_path
            if candidate.exists():
                return candidate.resolve()
        return resolved

    def resolve_filename(self, name_or_path: str, is_directory: Optional[bool] = None) -> Path:
        return FileSearchService.resolve(name_or_path, is_directory)

    def move_file(self, source: str, destination: Optional[str] = None) -> str:
        src = self.resolve_filename(source)
        if not src.exists():
            raise FileNotFoundError(f"Source path '{source}' not found (resolved: '{src}').")
            
        if not destination:
            title = f"Where would you like me to move '{src.name}'?\nExamples:\n* Documents\n* Downloads\n* Desktop\n* Custom path"
            from aether.api.prompt import prompt_user_sync
            destination = prompt_user_sync(title, []).strip()
            if not destination or destination.lower() in ('cancel', 'cancle', 'c', 'q', 'quit', 'exit', 'abort'):
                raise ValueError("Destination is required to move a file.")
                
        dst = self.resolve_path(destination)
        if dst.is_dir():
            dst_final = dst / src.name
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst_final = dst

        shutil.move(str(src), str(dst_final))
        
        remove_from_index(src)
        add_to_index(dst_final)
        return f"Successfully moved '{src.name}' from '{src}' to '{dst_final}'"

    def copy_file(self, source: str, destination: Optional[str] = None) -> str:
        src = self.resolve_filename(source)
        if not src.exists():
            raise FileNotFoundError(f"Source file '{source}' not found (resolved: '{src}').")
            
        if src.is_dir():
            raise IsADirectoryError("Copy file tool only supports files.")

        if not destination:
            title = f"Where would you like me to copy '{src.name}'?\nExamples:\n* Documents\n* Downloads\n* Desktop\n* Custom path"
            from aether.api.prompt import prompt_user_sync
            destination = prompt_user_sync(title, []).strip()
            if not destination or destination.lower() in ('cancel', 'cancle', 'c', 'q', 'quit', 'exit', 'abort'):
                raise ValueError("Destination is required to copy a file.")
                
        dst = self.resolve_path(destination)
        if dst.is_dir():
            dst_final = dst / src.name
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst_final = dst

        shutil.copy2(str(src), str(dst_final))
        add_to_index(dst_final)
        return f"Successfully copied '{src.name}' from '{src}' to '{dst_final}'"

    def rename_file(self, source: str, new_name: str) -> str:
        target = self.resolve_filename(source)
        if not target.exists():
            raise FileNotFoundError(f"Target '{source}' not found (resolved: '{target}').")
            
        if "/" in new_name or "\\" in new_name:
            raise ValueError("new_name parameter must be a filename, not a full path. Use move_file for moving.")
            
        if target.is_file() and target.suffix and not Path(new_name).suffix:
            new_name = new_name + target.suffix

        dest = target.parent / new_name
        target.rename(dest)
        
        remove_from_index(target)
        add_to_index(dest)
        return f"Successfully renamed '{target.name}' to '{new_name}' (path: '{dest}')"

    def delete_file(self, path: str) -> str:
        target = self.resolve_filename(path, is_directory=False)
        if not target.exists():
            raise FileNotFoundError(f"File '{path}' not found (resolved: '{target}').")
            
        send2trash.send2trash(str(target))
        remove_from_index(target)
        return f"Successfully deleted '{target.name}' (moved to Trash)."

    def open_file(self, path: str) -> str:
        target = self.resolve_filename(path, is_directory=False)
        if not target.exists():
            raise FileNotFoundError(f"File '{path}' not found (resolved: '{target}').")
            
        subprocess.run(["open", str(target)], check=True)
        return f"Successfully opened file '{target.name}' in its default viewer."

    def create_folder(self, folder_name: str, location: Optional[str] = None) -> str:
        if location and location.startswith("_ALREADY_OPENED_:"):
            dest_path = location.split("_ALREADY_OPENED_:", 1)[1]
            return f"Successfully opened existing folder at '{dest_path}' (Deferred creation)."

        create_another = False
        if location and "?create_another=true" in location:
            location = location.replace("?create_another=true", "")
            create_another = True

        from aether.api.prompt import prompt_user_sync

        if not location:
            title = f"Where would you like to create the folder '{folder_name}'?"
            options = ["Desktop", "Downloads", "Documents", "Current Working Directory", "Custom Path"]
            choice = prompt_user_sync(title, options).strip()
            if choice == "1":
                location = str(PlatformPaths.get_desktop())
            elif choice == "2":
                location = str(PlatformPaths.get_downloads())
            elif choice == "3":
                location = str(PlatformPaths.get_documents())
            elif choice == "4":
                location = os.getcwd()
            elif choice == "5":
                location = prompt_user_sync("Enter custom directory path:", []).strip()
                if not location:
                    raise ValueError("Location path is required.")
            else:
                if choice:
                    location = choice
                else:
                    location = os.getcwd()

        target_dir = self.resolve_path(location)
        target = target_dir / folder_name
        
        if not create_another:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT absolute_path, relative_location FROM indexed_files WHERE filename = ? AND is_directory = 1", (folder_name,))
            rows = cursor.fetchall()
            conn.close()
            
            if rows:
                title = f"A folder named '{folder_name}' already exists. What would you like to do?"
                options = ["Choose Existing Folder", "Create Another", "Cancel"]
                choice = prompt_user_sync(title, options).strip()
                
                if choice == '1' or choice.lower().startswith("choose") or choice.lower().startswith("open"):
                    if len(rows) == 1:
                        target = Path(rows[0]["absolute_path"])
                    else:
                        title_select = f"Which '{folder_name}' folder would you like to choose?"
                        select_options = [r[0] for r in rows]
                        select_choice = prompt_user_sync(title_select, select_options).strip()
                        if select_choice.isdigit():
                            idx = int(select_choice) - 1
                            if 0 <= idx < len(rows):
                                target = Path(rows[idx][0])
                            else:
                                raise ValueError("Invalid selection.")
                        else:
                            found = False
                            for r in rows:
                                if select_choice.lower() == r[0].lower():
                                    target = Path(r[0])
                                    found = True
                                    break
                            if not found:
                                raise ValueError("Invalid selection.")
                    return f"Successfully selected existing folder at '{target}'"
                elif choice == '2' or choice.lower().startswith("create"):
                    location = prompt_user_sync("Enter the location path where you want to create the new folder:", []).strip()
                    if not location or location.lower() in ('cancel', 'cancle', 'c', 'q', 'quit', 'exit', 'abort'):
                        raise ValueError("Location is required.")
                    target = self.resolve_path(location) / folder_name
                else:
                    raise ValueError("Operation cancelled by user.")

        if target.exists():
            if target.is_dir():
                return f"Folder '{target}' already exists."
            else:
                raise FileExistsError(f"A file already exists at '{target}'.")
                
        target.mkdir(parents=True, exist_ok=True)
        add_to_index(target)
        return f"Successfully created folder at '{target}'"

    def create_file(self, filename: str, location: Optional[str] = None) -> str:
        if location and location.startswith("_ALREADY_OPENED_:"):
            dest_path = location.split("_ALREADY_OPENED_:", 1)[1]
            return f"Successfully opened existing file at '{dest_path}' (Deferred creation)."

        create_another = False
        if location and "?create_another=true" in location:
            location = location.replace("?create_another=true", "")
            create_another = True

        from aether.api.prompt import prompt_user_sync

        if not location:
            title = f"Where would you like to create the file '{filename}'?"
            options = ["Desktop", "Downloads", "Documents", "Current Working Directory", "Custom Path"]
            choice = prompt_user_sync(title, options).strip()
            if choice == "1":
                location = str(PlatformPaths.get_desktop())
            elif choice == "2":
                location = str(PlatformPaths.get_downloads())
            elif choice == "3":
                location = str(PlatformPaths.get_documents())
            elif choice == "4":
                location = os.getcwd()
            elif choice == "5":
                location = prompt_user_sync("Enter custom directory path:", []).strip()
                if not location:
                    raise ValueError("Location path is required.")
            else:
                if choice:
                    location = choice
                else:
                    location = os.getcwd()

        target_dir = self.resolve_path(location)
        target = target_dir / filename
        
        if not create_another:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT absolute_path, relative_location FROM indexed_files WHERE filename = ? AND is_directory = 0", (filename,))
            rows = cursor.fetchall()
            conn.close()
            
            if rows:
                title = f"A file named '{filename}' already exists. What would you like to do?"
                options = ["Choose Existing File", "Create Another", "Cancel"]
                choice = prompt_user_sync(title, options).strip()
                
                if choice == '1' or choice.lower().startswith("choose") or choice.lower().startswith("open"):
                    if len(rows) == 1:
                        target = Path(rows[0]["absolute_path"])
                    else:
                        title_select = f"Which '{filename}' file would you like to choose?"
                        select_options = [r[0] for r in rows]
                        select_choice = prompt_user_sync(title_select, select_options).strip()
                        if select_choice.isdigit():
                            idx = int(select_choice) - 1
                            if 0 <= idx < len(rows):
                                target = Path(rows[idx][0])
                            else:
                                raise ValueError("Invalid selection.")
                        else:
                            found = False
                            for r in rows:
                                if select_choice.lower() == r[0].lower():
                                    target = Path(r[0])
                                    found = True
                                    break
                            if not found:
                                raise ValueError("Invalid selection.")
                    return f"Successfully selected existing file at '{target}'"
                elif choice == '2' or choice.lower().startswith("create"):
                    location = prompt_user_sync("Enter the location path where you want to create the new file:", []).strip()
                    if not location or location.lower() in ('cancel', 'cancle', 'c', 'q', 'quit', 'exit', 'abort'):
                        raise ValueError("Location is required.")
                    target = self.resolve_path(location) / filename
                else:
                    raise ValueError("Operation cancelled by user.")

        if target.exists():
            if target.is_file():
                return f"File '{target}' already exists."
            else:
                raise FileExistsError(f"A directory already exists at '{target}'.")
                
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch(exist_ok=True)
        add_to_index(target)
        return f"Successfully created file at '{target}'"

    def delete_folder(self, folder_name: str) -> str:
        target = self.resolve_filename(folder_name, is_directory=True)
        if not target.exists():
            raise FileNotFoundError(f"Folder '{folder_name}' not found (resolved: '{target}').")
            
        send2trash.send2trash(str(target))
        remove_from_index(target)
        return f"Successfully deleted folder '{target.name}' and its contents (moved to Trash)."

    def list_directory(self, path: Optional[str] = None) -> str:
        if not path:
            title = "Specify the directory path to list (or press Enter to list current working directory):"
            from aether.api.prompt import prompt_user_sync
            path = prompt_user_sync(title, []).strip()
            if not path or path.lower() in ('cancel', 'cancle', 'c', 'q', 'quit', 'exit', 'abort'):
                path = os.getcwd()
                
        target = self.resolve_filename(path, is_directory=True)
        items = list(target.iterdir())
        if not items:
            return f"Directory '{target}' is empty."
            
        lines = [f"Contents of '{target}':"]
        for item in items:
            prefix = "[DIR] " if item.is_dir() else "[FILE]"
            lines.append(f"  {prefix} {item.name}")
        return "\n".join(lines)

    def file_info(self, path: str) -> str:
        target = self.resolve_filename(path, is_directory=False)
        if not target.exists():
            raise FileNotFoundError(f"File '{path}' not found (resolved: '{target}').")
            
        stat = target.stat()
        size_bytes = stat.st_size
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        ext = target.suffix
        
        if size_bytes < 1024:
            size_str = f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            size_str = f"{size_bytes / 1024:.2f} KB"
        else:
            size_str = f"{size_bytes / (1024 * 1024):.2f} MB"
            
        return (
            f"File Metadata for '{target.name}':\n"
            f"  Absolute Path : {target}\n"
            f"  Size          : {size_str}\n"
            f"  Extension     : {ext}\n"
            f"  Modified Date : {mtime}"
        )

    def append_file(self, filename: str, text: str) -> str:
        target = self.resolve_filename(filename, is_directory=False)
        if not target.exists():
            raise FileNotFoundError(f"File '{filename}' not found (resolved: '{target}').")
        
        with open(target, "a", encoding="utf-8") as f:
            f.write("\n" + text)
        
        add_to_index(target)
        return f"Successfully appended content to '{target.name}'"

    def read_file_content(self, file_path: str) -> dict:
        supported_extensions = {".txt", ".md", ".py", ".json", ".csv", ".log"}
        p = self.resolve_filename(file_path, is_directory=False)
        if p.suffix.lower() not in supported_extensions:
            return {
                "success": False,
                "message": f"Unsupported file format '{p.suffix}'. Supported formats: {', '.join(supported_extensions)}"
            }

        if not p.exists():
            return {
                "success": False,
                "message": f"File not found at '{file_path}' (resolved: '{p}')."
            }
        if not p.is_file():
            return {
                "success": False,
                "message": f"Path '{file_path}' is not a file (resolved: '{p}')."
            }

        size_bytes = p.stat().st_size
        content = ""
        detected_encoding = None
        encodings_to_try = ["utf-8", "utf-8-sig", "cp1252", "latin-1", "utf-16"]
        
        for enc in encodings_to_try:
            try:
                with open(p, "r", encoding=enc) as f:
                    content = f.read(10005)
                detected_encoding = enc
                break
            except UnicodeDecodeError:
                continue

        if detected_encoding is None:
            return {
                "success": False,
                "message": "Failed to decode file with standard encodings."
            }

        return {
            "success": True,
            "message": "File read successfully.",
            "data": {
                "content": content[:10000],
                "size_bytes": size_bytes,
                "encoding": detected_encoding
            }
        }

    def compress_files(self, sources: List[str], output: str) -> str:
        out_archive = self.resolve_path(output)
        if not out_archive.name.lower().endswith(".zip"):
            out_archive = out_archive.with_suffix(".zip")
            
        title = f"Where would you like to store the zip file '{out_archive.name}'?"
        options = ["Desktop", "Downloads", "Documents", "Custom Path"]
        from aether.api.prompt import prompt_user_sync
        choice = prompt_user_sync(title, options).strip()
        
        if choice == "1":
            out_archive = PlatformPaths.get_desktop() / out_archive.name
        elif choice == "2":
            out_archive = PlatformPaths.get_downloads() / out_archive.name
        elif choice == "3":
            out_archive = PlatformPaths.get_documents() / out_archive.name
        elif choice == "4":
            custom_path = prompt_user_sync("Enter custom directory path or full zip file path:", []).strip()
            if custom_path:
                custom_p = self.resolve_path(custom_path)
                if custom_p.is_dir() or not custom_p.suffix:
                    out_archive = custom_p / out_archive.name
                else:
                    out_archive = custom_p
        elif choice:
            custom_p = self.resolve_path(choice)
            if custom_p.is_dir() or not custom_p.suffix:
                out_archive = custom_p / out_archive.name
            else:
                out_archive = custom_p

        out_archive.parent.mkdir(parents=True, exist_ok=True)
        
        resolved_sources = []
        for p_str in sources:
            try:
                p = self.resolve_filename(p_str)
                if p.exists():
                    resolved_sources.append(p)
            except Exception as e:
                logger.warning(f"File/folder '{p_str}' skipped for compression: {e}")
                
        if not resolved_sources:
            raise FileNotFoundError("None of the sources to compress were found.")

        with zipfile.ZipFile(out_archive, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for p in resolved_sources:
                if p.is_file():
                    zipf.write(p, p.name)
                elif p.is_dir():
                    for root, _, files in os.walk(p):
                        for file in files:
                            file_path = Path(root) / file
                            archive_name = file_path.relative_to(p.parent)
                            zipf.write(file_path, archive_name)
                            
        add_to_index(out_archive)
        return f"Successfully compressed files into '{out_archive}'"

    def extract_archive(self, archive: str, destination: Optional[str] = None) -> str:
        arc_path = self.resolve_filename(archive)
        if not arc_path.exists():
            raise FileNotFoundError(f"Archive file '{archive}' not found (resolved: '{arc_path}').")
            
        if not destination:
            title = f"Where would you like me to extract '{arc_path.name}'?\nExamples:\n* Documents\n* Downloads\n* Desktop\n* Custom path"
            from aether.api.prompt import prompt_user_sync
            destination = prompt_user_sync(title, []).strip()
            if not destination or destination.lower() in ('cancel', 'cancle', 'c', 'q', 'quit', 'exit', 'abort'):
                raise ValueError("Destination is required to extract an archive.")
                
        dst = self.resolve_path(destination)
        dst.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(arc_path, 'r') as zipf:
            zipf.extractall(dst)
            
        add_to_index(dst)
        return f"Successfully extracted archive '{arc_path.name}' into '{dst}'"

    def extract_text_from_image(self, path: str) -> dict:
        try:
            logger.info(f"Starting extract_text_from_image for path: {path}")
            p = self.resolve_filename(path, is_directory=False)
            if not p.exists():
                return {
                    "success": False,
                    "message": f"Image file not found at '{path}' (resolved: '{p}')."
                }
            if not p.is_file():
                return {
                    "success": False,
                    "message": f"Path '{path}' is not a file (resolved: '{p}')."
                }

            try:
                with Image.open(p) as img:
                    img.verify()
            except Exception as img_err:
                return {
                    "success": False,
                    "message": f"Unsupported or corrupt image format: {str(img_err)}"
                }

            with Image.open(p) as img:
                extracted_text = pytesseract.image_to_string(img)

            cleaned_text = " ".join(extracted_text.split()).strip()
            return {
                "success": True,
                "message": "Text extracted successfully.",
                "data": {
                    "text": cleaned_text
                }
            }
        except pytesseract.TesseractNotFoundError:
            return {
                "success": False,
                "message": "Tesseract OCR engine is not installed or not found in system path. Please install Tesseract-OCR."
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"OCR extraction failed: {str(e)}"
            }
