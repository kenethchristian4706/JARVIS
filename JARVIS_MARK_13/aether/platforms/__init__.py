"""
platform/__init__.py

Entrypoint for the Aether Platform Abstraction Layer.
Exports the active platform singleton instance.
"""

from aether.platforms.common.platform_factory import get_platform_instance

platform = get_platform_instance()
