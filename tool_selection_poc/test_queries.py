"""
test_queries.py

This module contains the evaluation queries used for benchmarking.
These queries must not be included in tools.py to ensure unbiased evaluation.
"""

TEST_QUERIES = [
    ("Could you please open Chrome for me?", "open_app"),
    ("I need to use VS Code.", "open_app"),
    ("Can you launch my browser?", "open_app"),
    ("Please close Spotify.", "close_app"),
    ("Terminate Discord.", "close_app"),
    ("Find my DevOps presentation.", "search_file"),
    ("Where did I save my resume?", "search_file"),
    ("Open assignment.pdf.", "open_file"),
    ("Show me notes.txt.", "open_file"),
    ("Create a file named meeting_notes.txt.", "create_file"),
    ("Make a document called todo.txt.", "create_file"),
    ("Move report.pdf into Downloads.", "move_file"),
    ("Transfer notes.txt to Desktop.", "move_file"),
    ("Create a folder named Work.", "create_folder"),
    ("Make a directory called AI.", "create_folder"),
    ("Open Notepad and write hello everyone.", "open_notepad_and_write"),
    ("Launch Notepad and type shopping list.", "open_notepad_and_write"),
    ("Set sound to 40 percent.", "set_volume"),
    ("Adjust volume to 80.", "set_volume"),
    ("Capture my screen.", "take_screenshot"),
    ("Take a snapshot of the display.", "take_screenshot"),
    ("Turn off my computer.", "shutdown_system"),
    ("Power down the machine.", "shutdown_system"),

    # Harder and more ambiguous queries
    ("Save all open work and lock down the computer screen.", "lock_system"),
    ("Log out of my user session right away.", "logout_user"),
    ("Put the system into sleep state.", "sleep_system"),
    ("Make the computer completely quiet by muting.", "mute_volume"),
    ("Turn the sound back on please.", "unmute_volume"),
    ("Make display brightness 100% since it is too dark.", "set_brightness"),
    ("Dim the screen light a bit.", "decrease_brightness"),
    ("Copy the text 'Aether project' to the clipboard.", "copy_to_clipboard"),
    ("Show me the content currently stored in the clipboard.", "read_clipboard"),
    ("Empty the system clipboard completely.", "clear_clipboard"),
    ("Search for files discussing machine learning algorithms.", "semantic_file_search"),
    ("Show me the files I accessed in the last 24 hours.", "recent_files"),
    ("Find all files on my computer with a .pdf extension.", "files_by_extension"),
    ("Show me files created yesterday.", "files_by_date"),
    ("Rename draft.docx to final_version.docx.", "rename_file"),
    ("Duplicate report.pdf inside the Backup folder.", "copy_file"),
    ("Delete the folder named test_data.", "delete_folder"),
    ("Search wikipedia.org for quantum computing.", "website_search"),
    ("Look up python tutorial on Google.", "google_search"),
    ("Search YouTube for mechanical keyboard reviews.", "youtube_search"),
    ("Close the browser tab showing stackoverflow.", "close_tab"),
    ("Switch to the tab with github.com.", "switch_tab"),
    ("Scroll down to the bottom of the page.", "scroll_page")
]
