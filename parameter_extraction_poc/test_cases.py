"""
test_cases.py

This module contains the dataset of 17 evaluation test cases for parameter extraction.
Each case contains: (tool_name, query, expected_json)
"""

TEST_CASES = [
    (
        "open_app",
        "Open Chrome",
        {"app_name": "chrome"}
    ),
    (
        "open_app",
        "Could you launch VS Code for me?",
        {"app_name": "vs code"}
    ),
    (
        "open_app",
        "Start Spotify",
        {"app_name": "spotify"}
    ),
    (
        "open_notepad_and_write",
        "Open Notepad and write hello world",
        {
            "app_name": "notepad",
            "text": "hello world"
        }
    ),
    (
        "open_notepad_and_write",
        "Launch Notepad and type meeting notes",
        {
            "app_name": "notepad",
            "text": "meeting notes"
        }
    ),
    (
        "open_notepad_and_write",
        "Open Notepad and jot down buy milk",
        {
            "app_name": "notepad",
            "text": "buy milk"
        }
    ),
    (
        "create_file",
        "Create notes.txt",
        {
            "filename": "notes.txt"
        }
    ),
    (
        "create_file",
        "Make a file called report.docx",
        {
            "filename": "report.docx"
        }
    ),
    (
        "move_file",
        "Move report.pdf to Downloads",
        {
            "source": "report.pdf",
            "destination": "Downloads"
        }
    ),
    (
        "move_file",
        "Transfer notes.txt into Desktop",
        {
            "source": "notes.txt",
            "destination": "Desktop"
        }
    ),
    (
        "create_folder",
        "Create folder AI Projects",
        {
            "folder_name": "AI Projects"
        }
    ),
    (
        "create_folder",
        "Make a directory called Work",
        {
            "folder_name": "Work"
        }
    ),
    (
        "set_volume",
        "Set volume to 50%",
        {
            "volume": 50
        }
    ),
    (
        "set_volume",
        "Change sound to 20 percent",
        {
            "volume": 20
        }
    ),
    (
        "set_volume",
        "Adjust volume to 80",
        {
            "volume": 80
        }
    ),
    (
        "shutdown_system",
        "Turn off my computer",
        {}
    ),
    (
        "shutdown_system",
        "Shutdown the PC",
        {}
    ),
    (
        "open_app",
        "Hey assistant, it would be awesome if you could open Google Chrome for me right now please.",
        {"app_name": "Google Chrome"}
    ),
    (
        "open_app",
        "Please launch the application 'Microsoft Edge (x64)'",
        {"app_name": "Microsoft Edge (x64)"}
    ),
    (
        "open_notepad_and_write",
        "Open Notepad and write: 'Hello! Please buy: 1. Milk, 2. Bread.'",
        {
            "app_name": "Notepad",
            "text": "Hello! Please buy: 1. Milk, 2. Bread."
        }
    ),
    (
        "open_notepad_and_write",
        "Open notepad and jot down: Neural networks are powerful models.",
        {
            "app_name": "notepad",
            "text": "Neural networks are powerful models."
        }
    ),
    (
        "create_file",
        "Create a file named my-cool-notes_v2.config.json",
        {"filename": "my-cool-notes_v2.config.json"}
    ),
    (
        "create_file",
        "Can you make a new document called '.gitignore'?",
        {"filename": ".gitignore"}
    ),
    (
        "move_file",
        "Transfer the document located at D:\\Projects\\report.pdf to E:\\Backups\\2026",
        {
            "source": "D:\\Projects\\report.pdf",
            "destination": "E:\\Backups\\2026"
        }
    ),
    (
        "move_file",
        "Put the file presentation.pptx into the folder /Users/lenovo/Documents/Shared",
        {
            "source": "presentation.pptx",
            "destination": "/Users/lenovo/Documents/Shared"
        }
    ),
    (
        "create_folder",
        "I need a folder to store my notes for the upcoming science fair, call it Science Notes",
        {"folder_name": "Science Notes"}
    ),
    (
        "create_folder",
        "Make a new directory named 'AI_Model_Weights-v2'",
        {"folder_name": "AI_Model_Weights-v2"}
    ),
    (
        "set_volume",
        "Adjust the sound level all the way down to zero percent",
        {"volume": 0}
    ),
    (
        "set_volume",
        "Can you set the system volume to 95",
        {"volume": 95}
    ),
    (
        "set_volume",
        "Make it exactly half volume",
        {"volume": 50}
    )
]
