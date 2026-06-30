"""
registry/micro_categories.py

Defines the micro capability categories used by the Router model.
Maps each micro category to the corresponding candidate tools in the registry.
"""

from typing import Dict, List

MICRO_CATEGORY_TO_TOOLS: Dict[str, List[str]] = {
    "system.app.open": ["open_app"],
    "system.app.close": ["close_app"],
    "system.app.list": ["list_installed_apps"],
    "window.focus": ["switch_to_app"],
    "process.list": ["list_running_apps", "list_processes"],
    "file.move": ["move_file"],
    "file.copy": ["copy_file", "duplicate_file"],
    "file.rename": ["rename_file"],
    "file.delete": ["delete_file"],
    "file.search": ["search_files"],
    "file.open": ["open_file"],
    "directory.create": ["create_folder"],
    "file.create": ["create_file"],
    "directory.delete": ["delete_folder"],
    "directory.list": ["list_directory"],
    "file.info": ["file_info"],
    "file.write": ["append_file", "write_file"],
    "file.read": ["read_file_content"],
    "compression.zip": ["compress_files"],
    "compression.unzip": ["extract_archive"],
    "browser.search": ["search_web"],
    "browser.youtube": ["search_youtube"],
    "browser.open": ["open_url"],
    "browser.tab.open": ["open_new_tab"],
    "browser.tab.close": ["close_tab"],
    "browser.tab.list": ["list_tabs"],
    "browser.tab.switch": ["switch_tab"],
    "network.download": ["download_file"],
    "email.send": ["send_email"],
    "email.list": ["list_emails"],
    "email.read": ["read_email"],
    "system.power.shutdown": ["shutdown_pc"],
    "system.power.restart": ["restart_pc"],
    "system.power.sleep": ["sleep_pc"],
    "system.power.lock": ["lock_pc"],
    "system.volume.set": ["set_volume"],
    "system.volume.mute": ["mute_volume"],
    "system.volume.unmute": ["unmute_volume"],
    "system.volume.increase": ["increase_volume"],
    "system.volume.decrease": ["decrease_volume"],
    "screenshot.capture": ["take_screenshot"],
    "system.brightness.set": ["set_brightness"],
    "system.brightness.increase": ["increase_brightness"],
    "system.brightness.decrease": ["decrease_brightness"],
    "ocr.extract": ["extract_text_from_image"],
    "text.notepad.write": ["open_notepad_and_write"],
    "clipboard.clear": ["clear_clipboard"],
    "clipboard.read": ["get_clipboard"],
    "clipboard.write": ["set_clipboard"],
    "system.info.cpu": ["cpu_usage"],
    "system.info.ram": ["ram_usage"],
    "system.info.disk": ["disk_usage"],
    "system.info.battery": ["battery_status"],
    "system.info.network": ["network_status"],
    "system.info.processes": ["list_processes"],
    "system.info.resolution": ["get_screen_resolution"]
}

MICRO_CATEGORIES: List[str] = list(MICRO_CATEGORY_TO_TOOLS.keys())
