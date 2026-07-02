"""
platform/mac/aliases.py

macOS application alias maps.
"""

from aether.platforms.common.aliases import resolve_alias

def resolve_mac_alias(app_name: str) -> str:
    return resolve_alias(app_name, "mac")
