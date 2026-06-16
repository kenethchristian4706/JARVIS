import os

# Paths
DEMO_DIR = os.path.expanduser(os.path.join("~", "Desktop", "AetherDemo"))
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "file_index.db"))

# Models
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"

# Thresholds
CONFIDENCE_THRESHOLD = 0.35

# Dummy files setup (10 files of varied types)
DUMMY_FILES = {
    "report_q2_2024.pdf": "",
    "devops_migration_plan.pptx": "",
    "meeting_notes_march.txt": "Meeting notes from March...",
    "budget_2024.xlsx": "",
    "project_roadmap.docx": "",
    "team_photo.jpg": "",
    "backup_config.json": '{"version": "1.0"}',
    "old_draft.txt": "Draft content...",
    "invoice_april.pdf": "",
    "readme.md": "# AetherDemo\nTest files for Aether."
}
