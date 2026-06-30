"""
tools/system_tools.py

Implements handlers for system control:
shutdown_pc, restart_pc, sleep_pc, lock_pc, set_volume, mute_volume, set_brightness.
"""

import os
import time
import socket
import urllib.request
import psutil
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional
from ctypes import cast, POINTER
import comtypes
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import screen_brightness_control as sbc
import pyautogui
import pyperclip
import pygetwindow as gw

logger = logging.getLogger(__name__)

def _get_volume_interface() -> Optional[POINTER(IAudioEndpointVolume)]:
    """Retrieves the Windows audio volume interface."""
    try:
        comtypes.CoInitialize()
    except Exception:
        pass
    try:
        devices = AudioUtilities.GetSpeakers()
        if hasattr(devices, "Activate"):
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            return cast(interface, POINTER(IAudioEndpointVolume))
        elif hasattr(devices, "EndpointVolume"):
            return devices.EndpointVolume
        return None
    except Exception as e:
        logger.error(f"Error accessing audio endpoint: {e}")
        return None

def shutdown_pc() -> str:
    """Powers down the computer immediately."""
    os.system("shutdown /s /t 1")
    return "Shutdown command triggered successfully."

def restart_pc() -> str:
    """Restarts the computer immediately."""
    os.system("shutdown /r /t 1")
    return "Restart command triggered successfully."

def sleep_pc() -> str:
    """Places the computer into sleep/suspend mode."""
    # Rundll32 power command
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    return "System put to sleep successfully."

def lock_pc() -> str:
    """Locks the Windows user session workstation."""
    os.system("rundll32.exe user32.dll,LockWorkStation")
    return "System session locked successfully."

def set_volume(level: int) -> str:
    """Sets the system master volume to a value in 0-100."""
    vol = _get_volume_interface()
    if not vol:
        raise OSError("Audio control device is unavailable.")
        
    # Scale from [0, 100] to float [0.0, 1.0]
    scalar = float(level) / 100.0
    vol.SetMasterVolumeLevelScalar(scalar, None)
    return f"Master volume set to {level}%."

def mute_volume() -> str:
    """Mutes the master system volume."""
    vol = _get_volume_interface()
    if not vol:
        raise OSError("Audio control device is unavailable.")
        
    vol.SetMute(1, None)
    return "Master system audio muted successfully."

def unmute_volume() -> str:
    """Unmutes the master system volume."""
    vol = _get_volume_interface()
    if not vol:
        raise OSError("Audio control device is unavailable.")
        
    vol.SetMute(0, None)
    return "Master system audio unmuted successfully."

def set_brightness(level: int) -> str:
    """Sets display screen brightness to a value in 0-100."""
    try:
        sbc.set_brightness(level)
        return f"Display brightness set to {level}%."
    except Exception as e:
        # Desktop external monitors might fail software adjustment
        raise OSError(f"Failed to adjust monitor brightness: {e}")

def take_screenshot(save_path: str | None = None) -> dict:
    """
    Capture the entire screen and save it as a PNG image.
    If save_path is not provided, saves to ~/Pictures/Aether/Screenshots/
    with an automatically generated filename.
    """
    try:
        logger.info("Starting take_screenshot tool execution.")
        if save_path:
            from aether.tools.file_tools import resolve_path
            p = resolve_path(save_path)
            # If no extension or is an existing directory or ends with slash, treat as directory
            if p.suffix == "" or p.is_dir() or save_path.endswith("/") or save_path.endswith("\\"):
                p.mkdir(parents=True, exist_ok=True)
                filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                final_path = p / filename
            else:
                p.parent.mkdir(parents=True, exist_ok=True)
                final_path = p
        else:
            default_dir = Path.home() / "Pictures" / "Aether" / "Screenshots"
            default_dir.mkdir(parents=True, exist_ok=True)
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            final_path = default_dir / filename

        # Take screenshot and save it
        screenshot = pyautogui.screenshot()
        screenshot.save(str(final_path))
        
        saved_path_str = final_path.as_posix()
        logger.info(f"Screenshot saved successfully at: {saved_path_str}")
        return {
            "success": True,
            "message": "Screenshot saved successfully.",
            "data": {
                "path": saved_path_str
            }
        }
    except Exception as e:
        logger.error(f"Error during screenshot capture: {e}")
        return {
            "success": False,
            "message": f"Failed to capture screenshot: {str(e)}"
        }

def open_notepad_and_write(text: str) -> dict:
    """
    Launch Windows Notepad, wait until active, and write the provided text preserving line breaks.
    """
    try:
        logger.info("Starting open_notepad_and_write tool execution.")
        # Launch Notepad
        subprocess.Popen(["notepad.exe"])
        
        # Wait for Notepad window to become active
        notepad_window = None
        for _ in range(10):  # Wait up to 5 seconds
            windows = gw.getWindowsWithTitle("Notepad")
            if windows:
                notepad_window = windows[0]
                break
            time.sleep(0.5)
            
        if not notepad_window:
            logger.error("Notepad window did not open within the timeout.")
            return {
                "success": False,
                "message": "Notepad failed to open in a timely manner."
            }
            
        # Activate the window using Win32 API SetForegroundWindow and ThreadInput attachment
        try:
            hwnd = notepad_window._hWnd
            import win32gui
            import win32con
            import win32process
            
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, 
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)
            win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, 
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)
            
            fore_hwnd = win32gui.GetForegroundWindow()
            if fore_hwnd != hwnd:
                fore_thread = win32process.GetWindowThreadProcessId(fore_hwnd)[0]
                target_thread = win32process.GetWindowThreadProcessId(hwnd)[0]
                if fore_thread != target_thread:
                    try:
                        win32process.AttachThreadInput(fore_thread, target_thread, True)
                        win32gui.SetForegroundWindow(hwnd)
                        win32process.AttachThreadInput(fore_thread, target_thread, False)
                    except Exception:
                        pass
                else:
                    win32gui.SetForegroundWindow(hwnd)
            win32gui.SetActiveWindow(hwnd)
            time.sleep(0.5)  # Let activation complete
        except Exception as e:
            logger.warning(f"Failed to activate Notepad window using Win32 helper: {e}")
            # Fallback to pygetwindow activate
            try:
                notepad_window.activate()
                time.sleep(0.5)
            except Exception as e2:
                logger.warning(f"Fallback activation also failed: {e2}")
            
        # Write the text using pyautogui
        pyautogui.write(text)
        logger.info("Successfully wrote text to Notepad.")
        return {
            "success": True,
            "message": "Notepad opened and text inserted."
        }
    except Exception as e:
        logger.error(f"Error during notepad write operation: {e}")
        return {
            "success": False,
            "message": f"Failed to open Notepad and write text: {str(e)}"
        }

def clear_clipboard() -> dict:
    """
    Clear the Windows clipboard and verify it was cleared successfully.
    """
    try:
        logger.info("Starting clear_clipboard tool execution.")
        pyperclip.copy("")
        # Verify it was cleared
        clipboard_content = pyperclip.paste()
        if clipboard_content == "":
            logger.info("Clipboard cleared successfully.")
            return {
                "success": True,
                "message": "Clipboard cleared successfully."
            }
            
        logger.error(f"Clipboard verification failed. Found: {repr(clipboard_content)}")
        return {
            "success": False,
            "message": "Clipboard was not cleared successfully."
        }
    except Exception as e:
        logger.error(f"Error while clearing clipboard: {e}")
        return {
            "success": False,
            "message": f"Failed to clear clipboard: {str(e)}"
        }

def get_clipboard() -> dict:
    """
    Retrieve the current text content of the Windows clipboard.
    """
    try:
        logger.info("Starting get_clipboard tool execution.")
        content = pyperclip.paste()
        return {
            "success": True,
            "message": "Successfully retrieved clipboard content.",
            "data": {
                "content": content
            }
        }
    except Exception as e:
        logger.error(f"Error while retrieving clipboard content: {e}")
        return {
            "success": False,
            "message": f"Failed to retrieve clipboard content: {str(e)}"
        }

def set_clipboard(text: str) -> dict:
    """
    Copy specified text to the Windows clipboard.
    """
    try:
        logger.info(f"Starting set_clipboard tool execution for text: {text}")
        pyperclip.copy(text)
        # Verify it was copied
        clipboard_content = pyperclip.paste()
        if clipboard_content == text:
            logger.info("Text copied to clipboard successfully.")
            return {
                "success": True,
                "message": "Text copied to clipboard successfully."
            }
        else:
            logger.error("Clipboard verification failed.")
            return {
                "success": False,
                "message": "Failed to copy text to clipboard."
            }
    except Exception as e:
        logger.error(f"Error while copying text to clipboard: {e}")
        return {
            "success": False,
            "message": f"Failed to copy text to clipboard: {str(e)}"
        }

def increase_volume() -> str:
    """
    Increase the master playback volume by a default step of 10%.
    """
    vol = _get_volume_interface()
    if not vol:
        raise OSError("Audio control device is unavailable.")
    current_scalar = vol.GetMasterVolumeLevelScalar()
    current_level = int(round(current_scalar * 100))
    new_level = min(100, current_level + 10)
    vol.SetMasterVolumeLevelScalar(float(new_level) / 100.0, None)
    return f"Master volume set to {new_level}%."

def decrease_volume() -> str:
    """
    Decrease the master playback volume by a default step of 10%.
    """
    vol = _get_volume_interface()
    if not vol:
        raise OSError("Audio control device is unavailable.")
    current_scalar = vol.GetMasterVolumeLevelScalar()
    current_level = int(round(current_scalar * 100))
    new_level = max(0, current_level - 10)
    vol.SetMasterVolumeLevelScalar(float(new_level) / 100.0, None)
    return f"Master volume set to {new_level}%."

def increase_brightness() -> str:
    """
    Increase the display screen brightness by a default step of 10%.
    """
    try:
        brightness_list = sbc.get_brightness()
        if isinstance(brightness_list, list) and len(brightness_list) > 0:
            current = brightness_list[0]
        elif isinstance(brightness_list, int):
            current = brightness_list
        else:
            current = 50
        
        new_level = min(100, current + 10)
        sbc.set_brightness(new_level)
        return f"Display brightness set to {new_level}%."
    except Exception as e:
        raise OSError(f"Failed to adjust monitor brightness: {e}")

def decrease_brightness() -> str:
    """
    Decrease the display screen brightness by a default step of 10%.
    """
    try:
        brightness_list = sbc.get_brightness()
        if isinstance(brightness_list, list) and len(brightness_list) > 0:
            current = brightness_list[0]
        elif isinstance(brightness_list, int):
            current = brightness_list
        else:
            current = 50
        
        new_level = max(0, current - 10)
        sbc.set_brightness(new_level)
        return f"Display brightness set to {new_level}%."
    except Exception as e:
        raise OSError(f"Failed to adjust monitor brightness: {e}")


def cpu_usage() -> dict:
    """
    Return current CPU utilization metrics including overall usage, per-core usage,
    logical and physical core counts, and frequency (if available).
    """
    start_time = time.time()
    logger.info("Starting cpu_usage tool execution.")
    try:
        overall = round(psutil.cpu_percent(interval=0.1), 1)
        per_core = [round(x, 1) for x in psutil.cpu_percent(interval=0.1, percpu=True)]
        logical = psutil.cpu_count(logical=True)
        physical = psutil.cpu_count(logical=False)
        
        frequency = None
        try:
            freq = psutil.cpu_freq()
            if freq:
                frequency = {
                    "current": round(freq.current, 1) if freq.current else None,
                    "min": round(freq.min, 1) if freq.min else None,
                    "max": round(freq.max, 1) if freq.max else None
                }
        except Exception as freq_err:
            logger.warning(f"Failed to retrieve CPU frequency: {freq_err}")
            
        data = {
            "overall": overall,
            "per_core": per_core,
            "logical_cores": logical,
            "physical_cores": physical,
            "frequency": frequency
        }
        
        duration = time.time() - start_time
        logger.info(f"cpu_usage completed in {duration:.4f}s. Overall: {overall}%")
        return {
            "success": True,
            "message": f"CPU Usage retrieved successfully. Overall CPU: {overall}%.",
            "data": data
        }
    except Exception as e:
        logger.error(f"Error in cpu_usage tool: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Failed to retrieve CPU usage: {str(e)}"
        }


def ram_usage() -> dict:
    """
    Return current RAM memory usage metrics.
    """
    start_time = time.time()
    logger.info("Starting ram_usage tool execution.")
    try:
        mem = psutil.virtual_memory()
        
        total_bytes = mem.total
        used_bytes = mem.used
        available_bytes = mem.available
        percent = round(mem.percent, 1)
        
        total_gb = round(total_bytes / (1024 ** 3), 2)
        used_gb = round(used_bytes / (1024 ** 3), 2)
        available_gb = round(available_bytes / (1024 ** 3), 2)
        
        data = {
            "total_bytes": total_bytes,
            "used_bytes": used_bytes,
            "available_bytes": available_bytes,
            "percent": percent,
            "total_gb": total_gb,
            "used_gb": used_gb,
            "available_gb": available_gb
        }
        
        duration = time.time() - start_time
        logger.info(f"ram_usage completed in {duration:.4f}s. Percentage: {percent}%")
        return {
            "success": True,
            "message": f"RAM Usage: {percent}% used ({used_gb} GB / {total_gb} GB).",
            "data": data
        }
    except Exception as e:
        logger.error(f"Error in ram_usage tool: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Failed to retrieve RAM usage: {str(e)}"
        }


def disk_usage() -> dict:
    """
    Return storage information for all mounted physical drives.
    """
    start_time = time.time()
    logger.info("Starting disk_usage tool execution.")
    try:
        drives = []
        partitions = psutil.disk_partitions(all=False)
        
        for part in partitions:
            if not part.mountpoint:
                continue
            # Skip empty CD-ROMs or offline network/removable drives that raise PermissionError/OSError
            try:
                usage = psutil.disk_usage(part.mountpoint)
                total_bytes = usage.total
                used_bytes = usage.used
                free_bytes = usage.free
                percent = round(usage.percent, 1)
                
                total_gb = round(total_bytes / (1024 ** 3), 2)
                used_gb = round(used_bytes / (1024 ** 3), 2)
                free_gb = round(free_bytes / (1024 ** 3), 2)
                
                drives.append({
                    "drive": part.mountpoint,
                    "device": part.device,
                    "fstype": part.fstype,
                    "total_bytes": total_bytes,
                    "used_bytes": used_bytes,
                    "free_bytes": free_bytes,
                    "percent": percent,
                    "total_gb": total_gb,
                    "used_gb": used_gb,
                    "free_gb": free_gb
                })
            except (PermissionError, OSError) as pe:
                logger.warning(f"Skipped disk partition {part.mountpoint} due to access restriction: {pe}")
            except Exception as de:
                logger.warning(f"Failed to check disk usage for partition {part.mountpoint}: {de}")
                
        duration = time.time() - start_time
        logger.info(f"disk_usage completed in {duration:.4f}s. Drives count: {len(drives)}")
        
        drive_summaries = [f"{d['drive']} ({d['percent']}% used)" for d in drives]
        message = f"Disk space retrieved for drives: {', '.join(drive_summaries)}." if drives else "No mounted drives detected or accessible."
        
        return {
            "success": True,
            "message": message,
            "data": {
                "drives": drives
            }
        }
    except Exception as e:
        logger.error(f"Error in disk_usage tool: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Failed to retrieve Disk usage: {str(e)}"
        }


def battery_status() -> dict:
    """
    Return battery charge status, percentage, and estimated remaining time.
    """
    start_time = time.time()
    logger.info("Starting battery_status tool execution.")
    try:
        battery = psutil.sensors_battery()
        if not battery:
            duration = time.time() - start_time
            logger.info(f"battery_status completed in {duration:.4f}s. Result: No battery detected.")
            return {
                "success": True,
                "message": "No battery detected.",
                "data": {
                    "has_battery": False
                }
            }
            
        percent = round(battery.percent, 1)
        plugged = battery.power_plugged
        charging_status = "Charging" if plugged else "Discharging"
        secsleft = battery.secsleft
        
        if secsleft == psutil.POWER_TIME_UNLIMITED:
            remaining_time = "Unlimited (Plugged in)"
        elif secsleft == psutil.POWER_TIME_UNKNOWN:
            remaining_time = "Unknown"
        else:
            hours = secsleft // 3600
            minutes = (secsleft % 3600) // 60
            remaining_time = f"{hours}h {minutes}m"
            
        data = {
            "has_battery": True,
            "percentage": percent,
            "plugged_in": plugged,
            "charging_status": charging_status,
            "secs_remaining": secsleft,
            "remaining_time": remaining_time
        }
        
        duration = time.time() - start_time
        logger.info(f"battery_status completed in {duration:.4f}s. Percentage: {percent}%")
        return {
            "success": True,
            "message": f"Battery status: {percent}% charged, {charging_status}. Remaining time: {remaining_time}.",
            "data": data
        }
    except Exception as e:
        logger.error(f"Error in battery_status tool: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Failed to retrieve battery status: {str(e)}"
        }


def network_status() -> dict:
    """
    Return network status, hostname, local IP, internet connection, and upload/download bytes.
    """
    start_time = time.time()
    logger.info("Starting network_status tool execution.")
    try:
        hostname = socket.gethostname()
        
        # Get active local IPv4
        local_ip = "127.0.0.1"
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except Exception:
            try:
                local_ip = socket.gethostbyname(hostname)
            except Exception:
                pass
                
        # Connect check + Public IP lookup
        internet_connectivity = False
        public_ip = "Unknown"
        try:
            # Query ipify with a short timeout
            req = urllib.request.Request("https://api.ipify.org", headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=2.0) as response:
                public_ip = response.read().decode('utf-8').strip()
                internet_connectivity = True
        except Exception:
            # Try connection test to google public DNS
            try:
                socket.setdefaulttimeout(2.0)
                socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
                internet_connectivity = True
            except Exception:
                pass
                
        # IO Counters
        io_counters = psutil.net_io_counters()
        uploaded_bytes = io_counters.bytes_sent
        downloaded_bytes = io_counters.bytes_recv
        
        # Determine active interface name and status
        active_interface = "Unknown"
        interface_status = "Unknown"
        
        try:
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            
            for name, snics in addrs.items():
                for snic in snics:
                    if snic.family == socket.AF_INET and snic.address == local_ip:
                        active_interface = name
                        if name in stats:
                            interface_status = "Up" if stats[name].isup else "Down"
                        break
            
            if active_interface == "Unknown" and stats:
                for name, stat in stats.items():
                    if stat.isup and name != "lo":
                        active_interface = name
                        interface_status = "Up"
                        break
        except Exception as net_err:
            logger.warning(f"Error checking network interfaces: {net_err}")
            
        data = {
            "hostname": hostname,
            "local_ip": local_ip,
            "public_ip": public_ip,
            "internet_connectivity": internet_connectivity,
            "active_interface": active_interface,
            "interface_status": interface_status,
            "uploaded_bytes": uploaded_bytes,
            "downloaded_bytes": downloaded_bytes
        }
        
        duration = time.time() - start_time
        logger.info(f"network_status completed in {duration:.4f}s. Local IP: {local_ip}, Connected: {internet_connectivity}")
        return {
            "success": True,
            "message": f"Network status: Local IP: {local_ip}, Internet Connected: {internet_connectivity}, Public IP: {public_ip}.",
            "data": data
        }
    except Exception as e:
        logger.error(f"Error in network_status tool: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Failed to retrieve network status: {str(e)}"
        }


def list_processes(sort_by: Optional[str] = "cpu", limit: int = 20) -> dict:
    """
    List currently running processes with PID, name, CPU%, Memory%, and exe path.
    """
    start_time = time.time()
    logger.info(f"Starting list_processes tool execution: sort_by={sort_by}, limit={limit}")
    try:
        processes = []
        
        # Initial pass to set baseline CPU usage
        for proc in psutil.process_iter():
            try:
                proc.cpu_percent()
            except Exception:
                pass
                
        time.sleep(0.1)  # Tiny delay to allow CPU usage measurement
        
        # Second pass to retrieve values
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'exe']):
            try:
                cpu = proc.cpu_percent()
                info = proc.info
                processes.append({
                    "pid": info['pid'],
                    "name": info['name'] or "Unknown",
                    "cpu_percent": round(cpu, 1),
                    "memory_percent": round(info['memory_percent'] or 0.0, 1),
                    "exe_path": info['exe'] or "Inaccessible"
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception:
                continue
                
        # Perform sorting
        sort_key = sort_by.lower().strip() if sort_by else "cpu"
        if sort_key == "memory":
            processes.sort(key=lambda x: x["memory_percent"], reverse=True)
        elif sort_key == "name":
            processes.sort(key=lambda x: x["name"].lower())
        else:  # default cpu
            processes.sort(key=lambda x: x["cpu_percent"], reverse=True)
            
        limited_list = processes[:limit]
        
        duration = time.time() - start_time
        logger.info(f"list_processes completed in {duration:.4f}s. Active: {len(processes)}, Returned: {len(limited_list)}")
        return {
            "success": True,
            "message": f"Retrieved top {len(limited_list)} processes sorted by '{sort_key}'.",
            "data": {
                "processes": limited_list,
                "total_processes": len(processes)
            }
        }
    except Exception as e:
        logger.error(f"Error in list_processes tool: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Failed to list processes: {str(e)}"
        }


def get_screen_resolution() -> dict:
    """
    Return resolution bounds for primary monitor and all connected displays.
    """
    start_time = time.time()
    logger.info("Starting get_screen_resolution tool execution.")
    try:
        width, height = pyautogui.size()
        monitors = []
        
        try:
            import win32api
            import win32con
            
            monitor_list = win32api.EnumDisplayMonitors()
            for m in monitor_list:
                handle = m[0]
                rect = m[2]
                info = win32api.GetMonitorInfo(handle)
                is_primary = info.get("Flags", 0) & win32con.MONITORINFOF_PRIMARY != 0
                
                m_width = rect[2] - rect[0]
                m_height = rect[3] - rect[1]
                
                monitors.append({
                    "name": info.get("Device", "Unknown"),
                    "width": m_width,
                    "height": m_height,
                    "is_primary": is_primary,
                    "bounds": {
                        "left": rect[0],
                        "top": rect[1],
                        "right": rect[2],
                        "bottom": rect[3]
                    }
                })
        except Exception as enum_err:
            logger.warning(f"Failed to enumerate monitors via win32api: {enum_err}")
            # Fallback to single monitor representation using pyautogui dimensions
            monitors = [{
                "name": "Primary Monitor",
                "width": width,
                "height": height,
                "is_primary": True,
                "bounds": {
                    "left": 0,
                    "top": 0,
                    "right": width,
                    "bottom": height
                }
            }]
            
        data = {
            "width": width,
            "height": height,
            "monitor_count": len(monitors),
            "monitors": monitors
        }
        
        duration = time.time() - start_time
        logger.info(f"get_screen_resolution completed in {duration:.4f}s. Primary: {width}x{height}, Count: {len(monitors)}")
        return {
            "success": True,
            "message": f"Primary screen resolution: {width}x{height} (Total displays: {len(monitors)}).",
            "data": data
        }
    except Exception as e:
        logger.error(f"Error in get_screen_resolution tool: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Failed to retrieve display resolution: {str(e)}"
        }

