"""
platform/common/aliases.py

Provides common database mapping of colloquial app names to platform-specific executables.
"""

CROSS_PLATFORM_ALIASES = {
    "chrome": {
        "windows": "Google Chrome",
        "mac": "Google Chrome"
    },
    "google chrome": {
        "windows": "Google Chrome",
        "mac": "Google Chrome"
    },
    "edge": {
        "windows": "Microsoft Edge",
        "mac": "Microsoft Edge"
    },
    "vscode": {
        "windows": "Visual Studio Code",
        "mac": "Visual Studio Code"
    },
    "vs code": {
        "windows": "Visual Studio Code",
        "mac": "Visual Studio Code"
    },
    "code": {
        "windows": "Visual Studio Code",
        "mac": "Visual Studio Code"
    },
    "terminal": {
        "windows": "Windows PowerShell",
        "mac": "Terminal"
    },
    "powershell": {
        "windows": "Windows PowerShell",
        "mac": "Terminal"
    },
    "cmd": {
        "windows": "Command Prompt",
        "mac": "Terminal"
    },
    "explorer": {
        "windows": "File Explorer",
        "mac": "Finder"
    },
    "notepad": {
        "windows": "Notepad",
        "mac": "TextEdit"
    },
    "calculator": {
        "windows": "Calculator",
        "mac": "Calculator"
    },
    "paint": {
        "windows": "Paint",
        "mac": "Preview"
    },
    "excel": {
        "windows": "Excel",
        "mac": "Microsoft Excel"
    },
    "word": {
        "windows": "Word",
        "mac": "Microsoft Word"
    },
    "powerpoint": {
        "windows": "PowerPoint",
        "mac": "Microsoft PowerPoint"
    },
    "teams": {
        "windows": "ms-teams.exe",
        "mac": "Microsoft Teams"
    },
    "microsoft teams": {
        "windows": "ms-teams.exe",
        "mac": "Microsoft Teams"
    },
    "whatsapp": {
        "windows": "whatsapp:",
        "mac": "WhatsApp"
    },
    "whatsapp.root": {
        "windows": "whatsapp:",
        "mac": "WhatsApp"
    }
}

def resolve_alias(extracted_name: str, os_name: str) -> str:
    """Resolves colloquial extracted name to the platform name mapping."""
    clean_name = extracted_name.strip().lower()
    if clean_name in CROSS_PLATFORM_ALIASES:
        return CROSS_PLATFORM_ALIASES[clean_name].get(os_name, extracted_name)
    return extracted_name
