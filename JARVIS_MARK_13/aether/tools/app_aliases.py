"""
tools/app_aliases.py

Maps colloquial application names to normalized executable names or Start Menu entries.
Implements fuzzy matching using difflib for unrecognized apps.
"""

import difflib
import logging
from aether.validation.validators import scan_installed_applications

logger = logging.getLogger(__name__)

# Map colloquial aliases to normalized names
APP_ALIASES = {
    "chrome": "Google Chrome",
    "google chrome": "Google Chrome",
    "edge": "Microsoft Edge",
    "vscode": "Visual Studio Code",
    "vs code": "Visual Studio Code",
    "code": "Visual Studio Code",
    "terminal": "Windows PowerShell",
    "powershell": "Windows PowerShell",
    "cmd": "Command Prompt",
    "explorer": "File Explorer",
    "notepad": "Notepad",
    "calculator": "Calculator",
    "paint": "Paint",
    "excel": "Excel",
    "word": "Word",
    "powerpoint": "PowerPoint",
    "teams": "ms-teams.exe",
    "microsoft teams": "ms-teams.exe",
    "whatsapp": "whatsapp:",
    "whatsapp.root": "whatsapp:"
}

def resolve_app_name(extracted_name: str) -> str:
    """
    Resolves colloquial application names to registry titles.
    Installed applications take precedence.
    Checks case-insensitively, exact alias matching first, and fuzzy matches fallback.
    """
    clean_name = extracted_name.strip().lower()
    
    # Scan installed applications
    installed_apps = {}
    try:
        installed_apps = scan_installed_applications()
    except Exception as e:
        logger.warning(f"Registry scanning encountered error: {e}")
        
    installed_names = list(installed_apps.keys())

    # 1. Exact match in installed apps (installed applications take precedence)
    for name in installed_names:
        if clean_name == name:
            logger.info(f"Resolved exact installed match: '{extracted_name}' -> '{name.title()}'")
            return name.title()

    # 2. Exact match in aliases mapping
    if clean_name in APP_ALIASES:
        normalized = APP_ALIASES[clean_name]
        logger.info(f"Resolved alias: '{extracted_name}' -> '{normalized}'")
        return normalized

    # 2b. Substring match in installed apps (e.g. "firefox" in "mozilla firefox")
    if len(clean_name) >= 3:
        for name in installed_names:
            if clean_name in name:
                logger.info(f"Resolved substring installed match: '{extracted_name}' -> '{name.title()}'")
                return name.title()

    # 3. Fuzzy match installed applications using difflib
    matches_inst = difflib.get_close_matches(clean_name, installed_names, n=1, cutoff=0.8)
    if matches_inst:
        resolved = matches_inst[0].title()
        logger.info(f"Fuzzy matched installed app: '{extracted_name}' -> '{resolved}'")
        return resolved

    # 4. Fuzzy match aliases using difflib
    matches_alias = difflib.get_close_matches(clean_name, list(APP_ALIASES.keys()), n=1, cutoff=0.8)
    if matches_alias:
        resolved = APP_ALIASES[matches_alias[0]]
        logger.info(f"Fuzzy matched alias: '{extracted_name}' -> '{resolved}'")
        return resolved

    # 5. Default fallback: return original name formatted as Title Case
    return extracted_name.title()
