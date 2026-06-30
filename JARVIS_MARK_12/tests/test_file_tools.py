import os
import shutil
import time
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from aether.tools.file_tools import write_file, duplicate_file
from aether.tools.indexer import init_db

class TestFileTools(unittest.TestCase):
    def setUp(self):
        # Initialize a temporary directory for tests
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)
        # Ensure index database exists for tests (mocking or using db)
        os.environ["AETHER_TESTING"] = "1"
        init_db()

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    # --- write_file Tests ---

    def test_write_file_create_new(self):
        file_path = self.dir_path / "test.txt"
        res = write_file(str(file_path), "Hello World", encoding="utf-8", create_parent=False)
        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["bytes_written"], 11)
        self.assertFalse(res["data"]["overwritten"])
        self.assertTrue(file_path.exists())
        self.assertEqual(file_path.read_text(encoding="utf-8"), "Hello World")

    def test_write_file_overwrite_existing(self):
        file_path = self.dir_path / "overwrite.md"
        file_path.write_text("Old Content", encoding="utf-8")
        
        res = write_file(str(file_path), "New Content", encoding="utf-8", create_parent=False)
        self.assertTrue(res["success"])
        self.assertTrue(res["data"]["overwritten"])
        self.assertEqual(file_path.read_text(encoding="utf-8"), "New Content")

    def test_write_file_unsupported_extension(self):
        file_path = self.dir_path / "binary.zip"
        res = write_file(str(file_path), "dummy data", encoding="utf-8", create_parent=False)
        self.assertFalse(res["success"])
        self.assertIn("Unsupported extension", res["message"])
        self.assertFalse(file_path.exists())

    def test_write_file_invalid_encoding(self):
        file_path = self.dir_path / "encoding.txt"
        res = write_file(str(file_path), "content", encoding="invalid-encoding-name", create_parent=False)
        self.assertFalse(res["success"])
        self.assertIn("encoding", res["message"].lower())

    def test_write_file_missing_parent_no_create(self):
        file_path = self.dir_path / "missing_sub" / "file.txt"
        res = write_file(str(file_path), "content", encoding="utf-8", create_parent=False)
        self.assertFalse(res["success"])
        self.assertIn("Parent directory", res["message"])
        self.assertFalse(file_path.exists())

    def test_write_file_missing_parent_create(self):
        file_path = self.dir_path / "created_sub" / "file.txt"
        res = write_file(str(file_path), "content", encoding="utf-8", create_parent=True)
        self.assertTrue(res["success"])
        self.assertTrue(file_path.exists())
        self.assertEqual(file_path.read_text(encoding="utf-8"), "content")

    def test_write_file_permission_denied(self):
        file_path = self.dir_path / "perm.txt"
        # Mock open to raise PermissionError
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            res = write_file(str(file_path), "content", encoding="utf-8", create_parent=False)
            self.assertFalse(res["success"])
            self.assertIn("Permission denied", res["message"])

    def test_write_file_custom_encoding(self):
        file_path = self.dir_path / "utf16.txt"
        res = write_file(str(file_path), "Hello", encoding="utf-16", create_parent=False)
        self.assertTrue(res["success"])
        self.assertEqual(file_path.read_text(encoding="utf-16"), "Hello")

    # --- duplicate_file Tests ---

    def test_duplicate_file_no_destination(self):
        # Create a source file
        src = self.dir_path / "notes.txt"
        src.write_text("Hello duplicate", encoding="utf-8")
        
        # Duplicate with destination omitted
        res = duplicate_file(str(src), destination=None, overwrite=False)
        self.assertTrue(res["success"])
        
        expected_dst = self.dir_path / "notes - Copy.txt"
        self.assertTrue(expected_dst.exists())
        self.assertEqual(expected_dst.read_text(encoding="utf-8"), "Hello duplicate")
        self.assertEqual(res["data"]["destination"], str(expected_dst))

    def test_duplicate_file_multiple_times(self):
        src = self.dir_path / "report.md"
        src.write_text("report text", encoding="utf-8")
        
        res1 = duplicate_file(str(src), destination=None, overwrite=False)
        res2 = duplicate_file(str(src), destination=None, overwrite=False)
        res3 = duplicate_file(str(src), destination=None, overwrite=False)
        
        self.assertTrue(res1["success"])
        self.assertTrue(res2["success"])
        self.assertTrue(res3["success"])
        
        self.assertTrue((self.dir_path / "report - Copy.md").exists())
        self.assertTrue((self.dir_path / "report - Copy (2).md").exists())
        self.assertTrue((self.dir_path / "report - Copy (3).md").exists())

    def test_duplicate_file_destination_folder(self):
        src = self.dir_path / "source.txt"
        src.write_text("source content", encoding="utf-8")
        
        dest_dir = self.dir_path / "backup_folder"
        dest_dir.mkdir()
        
        res = duplicate_file(str(src), destination=str(dest_dir), overwrite=False)
        self.assertTrue(res["success"])
        
        expected_dst = dest_dir / "source.txt"
        self.assertTrue(expected_dst.exists())
        self.assertEqual(expected_dst.read_text(encoding="utf-8"), "source content")

    def test_duplicate_file_destination_file_overwrite_disabled(self):
        src = self.dir_path / "source.txt"
        src.write_text("source content", encoding="utf-8")
        
        dst = self.dir_path / "destination.txt"
        dst.write_text("existing content", encoding="utf-8")
        
        res = duplicate_file(str(src), destination=str(dst), overwrite=False)
        self.assertFalse(res["success"])
        self.assertIn("already exists", res["message"])
        self.assertEqual(dst.read_text(encoding="utf-8"), "existing content")

    def test_duplicate_file_destination_file_overwrite_enabled(self):
        src = self.dir_path / "source.txt"
        src.write_text("source content", encoding="utf-8")
        
        dst = self.dir_path / "destination.txt"
        dst.write_text("existing content", encoding="utf-8")
        
        res = duplicate_file(str(src), destination=str(dst), overwrite=True)
        self.assertTrue(res["success"])
        self.assertEqual(dst.read_text(encoding="utf-8"), "source content")

    def test_duplicate_file_source_missing(self):
        res = duplicate_file(str(self.dir_path / "nonexistent.txt"), destination=None, overwrite=False)
        self.assertFalse(res["success"])
        self.assertIn("not found", res["message"])

    def test_duplicate_file_permission_denied(self):
        src = self.dir_path / "source.txt"
        src.write_text("source content", encoding="utf-8")
        
        with patch("shutil.copy2", side_effect=PermissionError("Permission denied")):
            res = duplicate_file(str(src), destination=None, overwrite=False)
            self.assertFalse(res["success"])
            self.assertIn("Permission denied", res["message"])

    def test_duplicate_file_metadata_preserved(self):
        src = self.dir_path / "source.txt"
        src.write_text("source content", encoding="utf-8")
        
        # Set mtime back by 100 seconds
        orig_mtime = time.time() - 100
        os.utime(src, (orig_mtime, orig_mtime))
        
        res = duplicate_file(str(src), destination=None, overwrite=False)
        self.assertTrue(res["success"])
        
        dst = Path(res["data"]["destination"])
        dst_mtime = dst.stat().st_mtime
        
        # Verify timestamps are close enough (shutil.copy2 preserves them)
        self.assertAlmostEqual(orig_mtime, dst_mtime, places=2)

if __name__ == "__main__":
    unittest.main()
