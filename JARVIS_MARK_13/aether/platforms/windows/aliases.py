"""
platform/windows/aliases.py

Windows application alias maps.
"""

from aether.platforms.common.aliases import resolve_alias

def resolve_windows_alias(app_name: str) -> str:
    return resolve_alias(app_name, "windows")
