import unittest
from unittest.mock import patch, MagicMock
import psutil
import socket

from aether.tools.system_tools import (
    cpu_usage,
    ram_usage,
    disk_usage,
    battery_status,
    network_status,
    list_processes,
    get_screen_resolution
)

class TestSystemInfoTools(unittest.TestCase):

    def test_cpu_usage(self):
        res = cpu_usage()
        self.assertTrue(res["success"])
        self.assertIn("overall", res["data"])
        self.assertIn("per_core", res["data"])
        self.assertIn("logical_cores", res["data"])
        self.assertIn("physical_cores", res["data"])
        self.assertIn("frequency", res["data"])
        
        self.assertIsInstance(res["data"]["overall"], (int, float))
        self.assertIsInstance(res["data"]["per_core"], list)
        self.assertIsInstance(res["data"]["logical_cores"], int)

    def test_ram_usage(self):
        res = ram_usage()
        self.assertTrue(res["success"])
        self.assertIn("total_bytes", res["data"])
        self.assertIn("used_bytes", res["data"])
        self.assertIn("available_bytes", res["data"])
        self.assertIn("percent", res["data"])
        self.assertIn("total_gb", res["data"])
        self.assertIn("used_gb", res["data"])
        self.assertIn("available_gb", res["data"])
        
        self.assertIsInstance(res["data"]["total_bytes"], int)
        self.assertIsInstance(res["data"]["percent"], (int, float))
        self.assertIsInstance(res["data"]["total_gb"], (int, float))

    def test_disk_usage(self):
        res = disk_usage()
        self.assertTrue(res["success"])
        self.assertIn("drives", res["data"])
        self.assertIsInstance(res["data"]["drives"], list)
        
        if res["data"]["drives"]:
            drive = res["data"]["drives"][0]
            self.assertIn("drive", drive)
            self.assertIn("percent", drive)
            self.assertIn("total_gb", drive)
            self.assertIn("used_gb", drive)
            self.assertIn("free_gb", drive)

    def test_battery_status(self):
        res = battery_status()
        self.assertTrue(res["success"])
        self.assertIn("has_battery", res["data"])
        
        if res["data"]["has_battery"]:
            self.assertIn("percentage", res["data"])
            self.assertIn("plugged_in", res["data"])
            self.assertIn("charging_status", res["data"])
            self.assertIn("remaining_time", res["data"])

    def test_network_status(self):
        res = network_status()
        self.assertTrue(res["success"])
        self.assertIn("hostname", res["data"])
        self.assertIn("local_ip", res["data"])
        self.assertIn("public_ip", res["data"])
        self.assertIn("internet_connectivity", res["data"])
        self.assertIn("uploaded_bytes", res["data"])
        self.assertIn("downloaded_bytes", res["data"])
        
        self.assertIsInstance(res["data"]["hostname"], str)
        self.assertIsInstance(res["data"]["local_ip"], str)

    def test_list_processes(self):
        # Test default sorting and limit
        res = list_processes(limit=5)
        self.assertTrue(res["success"])
        self.assertIn("processes", res["data"])
        self.assertIn("total_processes", res["data"])
        
        processes = res["data"]["processes"]
        self.assertLessEqual(len(processes), 5)
        
        if processes:
            proc = processes[0]
            self.assertIn("pid", proc)
            self.assertIn("name", proc)
            self.assertIn("cpu_percent", proc)
            self.assertIn("memory_percent", proc)
            self.assertIn("exe_path", proc)

        # Test sorting by memory
        res_mem = list_processes(sort_by="memory", limit=5)
        self.assertTrue(res_mem["success"])
        p_mem = res_mem["data"]["processes"]
        if len(p_mem) > 1:
            self.assertGreaterEqual(p_mem[0]["memory_percent"], p_mem[-1]["memory_percent"])

    def test_get_screen_resolution(self):
        res = get_screen_resolution()
        self.assertTrue(res["success"])
        self.assertIn("width", res["data"])
        self.assertIn("height", res["data"])
        self.assertIn("monitor_count", res["data"])
        self.assertIn("monitors", res["data"])
        
        self.assertIsInstance(res["data"]["width"], int)
        self.assertIsInstance(res["data"]["height"], int)
        self.assertIsInstance(res["data"]["monitors"], list)
        self.assertGreaterEqual(len(res["data"]["monitors"]), 1)

    # --- Error handling test cases ---

    @patch("psutil.cpu_percent", side_effect=Exception("CPU metric failure"))
    def test_cpu_usage_error(self, mock_cpu):
        res = cpu_usage()
        self.assertFalse(res["success"])
        self.assertIn("Failed to retrieve CPU usage", res["message"])

    @patch("psutil.virtual_memory", side_effect=Exception("RAM metric failure"))
    def test_ram_usage_error(self, mock_ram):
        res = ram_usage()
        self.assertFalse(res["success"])
        self.assertIn("Failed to retrieve RAM usage", res["message"])

    @patch("psutil.disk_partitions", side_effect=Exception("Disk partition failure"))
    def test_disk_usage_error(self, mock_disk):
        res = disk_usage()
        self.assertFalse(res["success"])
        self.assertIn("Failed to retrieve Disk usage", res["message"])

    @patch("psutil.sensors_battery", side_effect=Exception("Battery sensors failure"))
    def test_battery_status_error(self, mock_battery):
        res = battery_status()
        self.assertFalse(res["success"])
        self.assertIn("Failed to retrieve battery status", res["message"])

    @patch("socket.gethostname", side_effect=Exception("Hostname retrieval failure"))
    def test_network_status_error(self, mock_socket):
        res = network_status()
        self.assertFalse(res["success"])
        self.assertIn("Failed to retrieve network status", res["message"])

    @patch("psutil.process_iter", side_effect=Exception("Process enumeration failure"))
    def test_list_processes_error(self, mock_proc):
        res = list_processes()
        self.assertFalse(res["success"])
        self.assertIn("Failed to list processes", res["message"])

    @patch("pyautogui.size", side_effect=Exception("Screen bounds failure"))
    def test_get_screen_resolution_error(self, mock_resolution):
        res = get_screen_resolution()
        self.assertFalse(res["success"])
        self.assertIn("Failed to retrieve display resolution", res["message"])

if __name__ == "__main__":
    unittest.main()
