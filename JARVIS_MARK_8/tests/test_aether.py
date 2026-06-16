"""
tests/test_aether.py

Unit testing suite verifying the tool selection preprocessor, Pydantic validation schemas,
database managers, and safety verification boundaries.
"""

import unittest
import os
import shutil
import tempfile
import sqlite3

from ai.tool_selector import preprocess_query, ToolSelector
from validation.schemas import TOOL_REGISTRY, OpenAppSchema, SetVolumeSchema
from permissions.safety_manager import get_tool_risk_level
from permissions.access_manager import check_permission, add_folder_permission, _session_permissions
from database.db_manager import get_db_connection, init_db

class TestAetherComponents(unittest.TestCase):
    
    def test_query_preprocessing(self):
        """
        Verifies query cleaning, alias normalization, and typo corrections.
        """
        self.assertEqual(preprocess_query("opne chorme"), "open chrome")
        self.assertEqual(preprocess_query("start vscode"), "start VS Code")
        self.assertEqual(preprocess_query("Google Chrome browser"), "Chrome")
        self.assertEqual(preprocess_query("Set volume to 40 percent!"), "set volume to 40 percent")
        
    def test_pydantic_schemas(self):
        """
        Validates schemas correct inputs and catches invalid inputs.
        """
        # Valid cases
        app_val = OpenAppSchema(app_name="spotify")
        self.assertEqual(app_val.app_name, "spotify")
        
        vol_val = SetVolumeSchema(volume=50)
        self.assertEqual(vol_val.volume, 50)
        
        # Invalid cases
        with self.assertRaises(Exception):
            SetVolumeSchema(volume=150) # ge=0, le=100
        with self.assertRaises(Exception):
            SetVolumeSchema(volume=-10)

    def test_safety_risk_mapping(self):
        """
        Tests that tools are correctly categorized by risk level.
        """
        self.assertEqual(get_tool_risk_level("open_app"), "low")
        self.assertEqual(get_tool_risk_level("create_file"), "medium")
        self.assertEqual(get_tool_risk_level("delete_file"), "high")
        self.assertEqual(get_tool_risk_level("shutdown_system"), "high")

    def test_database_initialization(self):
        """
        Checks that SQLite schemas compile correctly.
        """
        init_db()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Verify file_index table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='file_index'")
            self.assertIsNotNone(cursor.fetchone())
            
            # Verify installed_apps table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='installed_apps'")
            self.assertIsNotNone(cursor.fetchone())

    def test_access_manager_permissions(self):
        """
        Validates permission hierarchy matching.
        """
        init_db()
        temp_dir = os.path.normpath(tempfile.gettempdir())
        
        # Explicitly permit read only
        add_folder_permission(temp_dir, "read")
        
        # Should allow read operations
        self.assertTrue(check_permission(temp_dir, "read"))
        # Should block write operations
        self.assertFalse(check_permission(temp_dir, "read_write"))
        
        # Check session "Allow Once" permission override
        _session_permissions[temp_dir] = "read_write"
        self.assertTrue(check_permission(temp_dir, "read_write"))
        self.assertFalse(check_permission(temp_dir, "full_control"))
        
        # Clean up session permission state
        _session_permissions.pop(temp_dir, None)

if __name__ == "__main__":
    unittest.main()
