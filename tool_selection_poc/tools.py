"""
tools.py

This module contains the full catalog of Phase 1 tools for Aether's tool selection POC.
It contains 56 tools in total, each with a tool name, description, and example queries.
"""

TOOLS = [
    # ----------------------------------------------------
    # Category: Application Management (5 tools)
    # ----------------------------------------------------
    {
        "tool_name": "open_app",
        "description": "Open or launch an application installed on the computer.",
        "examples": [
            "Open Chrome",
            "Launch VS Code",
            "Start Spotify",
            "Open Discord",
            "Can you open Notepad for me?",
            "Please launch Calculator",
            "Bring up Visual Studio Code",
            "Start Chrome browser",
            "I want to use Spotify",
            "Open my text editor"
        ]
    },
    {
        "tool_name": "close_app",
        "description": "Close or terminate a running application.",
        "examples": [
            "Close Chrome",
            "Exit VS Code",
            "Terminate Spotify",
            "Can you close Discord?",
            "Please shut down Notepad",
            "Kill Calculator",
            "Stop Chrome browser",
            "Close my text editor"
        ]
    },
    {
        "tool_name": "switch_to_app",
        "description": "Switch the active window focus to a running application.",
        "examples": [
            "Switch to Chrome",
            "Focus VS Code",
            "Bring Spotify to the front",
            "Switch window to Discord",
            "Go to Notepad window",
            "Bring up my web browser window",
            "Change focus to Outlook",
            "Switch to the terminal app"
        ]
    },
    {
        "tool_name": "list_running_apps",
        "description": "List all applications currently running on the system.",
        "examples": [
            "What programs are running?",
            "List running applications",
            "Show active apps",
            "What is open right now?",
            "Show running tasks",
            "Give me a list of open windows",
            "Which apps are running on my PC?",
            "Show active processes"
        ]
    },
    {
        "tool_name": "list_installed_apps",
        "description": "List all applications installed on the computer.",
        "examples": [
            "List installed applications",
            "What software is installed?",
            "Show all programs",
            "List my apps",
            "What apps do I have?",
            "Show all installed software on my machine",
            "Check what apps are installed on this PC",
            "List all applications available on this computer"
        ]
    },

    # ----------------------------------------------------
    # Category: System Control (5 tools)
    # ----------------------------------------------------
    {
        "tool_name": "shutdown_system",
        "description": "Shut down the computer.",
        "examples": [
            "Shutdown the computer",
            "Turn off my PC",
            "Power off the system",
            "Shut down Windows"
        ]
    },
    {
        "tool_name": "restart_system",
        "description": "Restart or reboot the computer.",
        "examples": [
            "Restart my PC",
            "Reboot the system",
            "Restart computer",
            "Please reboot Windows",
            "Perform system reboot",
            "Restart my computer now",
            "Reboot the machine",
            "Trigger a system restart"
        ]
    },
    {
        "tool_name": "sleep_system",
        "description": "Put the computer into sleep mode.",
        "examples": [
            "Put my PC to sleep",
            "Go to sleep",
            "Suspend the computer",
            "Put system in sleep state",
            "Send PC to sleep mode",
            "Put computer to sleep",
            "Enter sleep state",
            "Hibernate or put the system to sleep"
        ]
    },
    {
        "tool_name": "lock_system",
        "description": "Lock the computer screen.",
        "examples": [
            "Lock my PC",
            "Lock the screen",
            "Lock my computer",
            "Secure my workspace",
            "Lock the Windows screen",
            "Go to the lock screen",
            "Lock the device",
            "Lock this machine"
        ]
    },
    {
        "tool_name": "logout_user",
        "description": "Log out the current user session.",
        "examples": [
            "Log out",
            "Sign out of my account",
            "Log me out",
            "Exit the current user session",
            "Log out the current user",
            "Sign off from Windows",
            "Sign out of the system",
            "Close my user session"
        ]
    },

    # ----------------------------------------------------
    # Category: Audio Settings (5 tools)
    # ----------------------------------------------------
    {
        "tool_name": "set_volume",
        "description": "Adjust the system volume.",
        "examples": [
            "Set volume to 50%",
            "Change volume to 20%",
            "Increase sound to 70%",
            "Lower volume to 10%"
        ]
    },
    {
        "tool_name": "increase_volume",
        "description": "Increase the system volume.",
        "examples": [
            "Turn up the volume",
            "Make it louder",
            "Increase sound",
            "Raise volume level",
            "Turn the sound up a bit",
            "Make the volume higher",
            "Boost the audio output",
            "Can you turn the volume up?"
        ]
    },
    {
        "tool_name": "decrease_volume",
        "description": "Decrease the system volume.",
        "examples": [
            "Turn down the volume",
            "Make it quieter",
            "Decrease sound",
            "Lower volume level",
            "Turn the sound down a bit",
            "Make the volume lower",
            "Reduce the audio output",
            "Can you turn the volume down?"
        ]
    },
    {
        "tool_name": "mute_volume",
        "description": "Mute the system audio.",
        "examples": [
            "Mute sound",
            "Mute the volume",
            "Silence the audio",
            "Turn off system sound",
            "Silence my PC",
            "Mute the speakers",
            "Go silent",
            "Disable audio output"
        ]
    },
    {
        "tool_name": "unmute_volume",
        "description": "Unmute the system audio.",
        "examples": [
            "Unmute sound",
            "Turn sound back on",
            "Restore volume",
            "Unmute audio",
            "Enable the audio sound",
            "Unmute the speaker output",
            "Bring back the sound",
            "Turn audio on"
        ]
    },

    # ----------------------------------------------------
    # Category: Display Brightness (3 tools)
    # ----------------------------------------------------
    {
        "tool_name": "set_brightness",
        "description": "Set the screen brightness to a specific percentage.",
        "examples": [
            "Set brightness to 60%",
            "Adjust brightness to 80",
            "Set screen brightness to 50%",
            "Change brightness to 30%",
            "Configure display brightness to 90 percent",
            "Adjust monitor brightness to 40%",
            "Set screen level to 75 percent brightness",
            "Make display brightness 100%"
        ]
    },
    {
        "tool_name": "increase_brightness",
        "description": "Increase the screen brightness.",
        "examples": [
            "Make the screen brighter",
            "Increase brightness",
            "Turn up brightness",
            "Brighten the screen",
            "Increase monitor brightness",
            "Increase display brightness",
            "Make the screen lighter",
            "Turn up screen brightness"
        ]
    },
    {
        "tool_name": "decrease_brightness",
        "description": "Decrease the screen brightness.",
        "examples": [
            "Make the screen dimmer",
            "Decrease brightness",
            "Turn down screen brightness",
            "Dim the screen",
            "Lower display brightness",
            "Dim the monitor",
            "Reduce screen light",
            "Make screen darker"
        ]
    },

    # ----------------------------------------------------
    # Category: Clipboard Operations (3 tools)
    # ----------------------------------------------------
    {
        "tool_name": "copy_to_clipboard",
        "description": "Copy specified text to the system clipboard.",
        "examples": [
            "Copy hello to clipboard",
            "Copy this text",
            "Copy password to clipboard",
            "Put this string on the clipboard",
            "Copy 'Aether' to system clipboard",
            "Save the following text to my clipboard",
            "Copy this link to clipboard",
            "Place this snippet in my clipboard"
        ]
    },
    {
        "tool_name": "read_clipboard",
        "description": "Read and retrieve the text currently stored in the clipboard.",
        "examples": [
            "Get clipboard contents",
            "What is in my clipboard?",
            "Read clipboard",
            "Paste from clipboard",
            "Show me what I copied",
            "Print clipboard text",
            "Retrieve clipboard contents",
            "Fetch the text from my clipboard"
        ]
    },
    {
        "tool_name": "clear_clipboard",
        "description": "Clear the system clipboard content.",
        "examples": [
            "Clear my clipboard",
            "Empty the clipboard",
            "Erase clipboard contents",
            "Wipe clipboard",
            "Clean the system clipboard",
            "Remove all data from my clipboard",
            "Reset clipboard",
            "Flush clipboard contents"
        ]
    },

    # ----------------------------------------------------
    # Category: File Management (7 tools)
    # ----------------------------------------------------
    {
        "tool_name": "search_file",
        "description": "Search for files or documents on the computer.",
        "examples": [
            "Find my resume",
            "Search for report.pdf",
            "Locate tax documents",
            "Where is presentation.pptx?",
            "Can you find notes.txt?",
            "Show me my DevOps resume",
            "Search for AI project files",
            "Find my assignment"
        ]
    },
    {
        "tool_name": "open_file",
        "description": "Open an existing file on the computer.",
        "examples": [
            "Open report.pdf",
            "Open my resume",
            "Launch presentation.pptx",
            "Open notes.txt",
            "Show me assignment.docx",
            "Open the tax document"
        ]
    },
    {
        "tool_name": "create_file",
        "description": "Create a new file.",
        "examples": [
            "Create notes.txt",
            "Make a new file called todo.txt",
            "Create report.docx",
            "Generate meeting_notes.txt",
            "Make a text file named ideas.txt"
        ]
    },
    {
        "tool_name": "delete_file",
        "description": "Delete or remove an existing file.",
        "examples": [
            "Delete report.pdf",
            "Remove notes.txt",
            "Delete my resume",
            "Trash assignment.docx",
            "Erase meeting_notes.txt",
            "Delete the file data.csv",
            "Remove logfile.log from the system",
            "Permanently delete tax.pdf"
        ]
    },
    {
        "tool_name": "rename_file",
        "description": "Rename an existing file.",
        "examples": [
            "Rename report.pdf to annual_report.pdf",
            "Change name of resume.docx to resume_v2.docx",
            "Rename notes.txt to todo.txt",
            "Give a new name to data.csv",
            "Rename the document invoice.pdf to invoice_paid.pdf",
            "Change file name from draft.txt to final.txt",
            "Change the name of presentation.pptx",
            "Modify file name of project.zip to archive.zip"
        ]
    },
    {
        "tool_name": "move_file",
        "description": "Move a file from one location to another.",
        "examples": [
            "Move report.pdf to Downloads",
            "Transfer notes.txt to Documents",
            "Move tax.pdf into Backup",
            "Put assignment.docx in Desktop"
        ]
    },
    {
        "tool_name": "copy_file",
        "description": "Copy a file to another location or name.",
        "examples": [
            "Copy report.pdf to Downloads",
            "Duplicate notes.txt in Documents",
            "Make a copy of tax.pdf in Backup",
            "Copy assignment.docx to the Desktop folder",
            "Create a duplicate of file.txt",
            "Copy photo.jpg to Pictures directory",
            "Duplicate report.pdf and rename it",
            "Copy data.csv to archive directory"
        ]
    },

    # ----------------------------------------------------
    # Category: Folder Management (3 tools)
    # ----------------------------------------------------
    {
        "tool_name": "create_folder",
        "description": "Create a new folder.",
        "examples": [
            "Create folder AI Projects",
            "Make a folder called Work",
            "Generate a directory named Resume",
            "Create a folder for DevOps"
        ]
    },
    {
        "tool_name": "delete_folder",
        "description": "Delete or remove an existing folder.",
        "examples": [
            "Delete folder AI Projects",
            "Remove directory Work",
            "Delete my empty folder",
            "Trash the Resume directory",
            "Remove the folder named test_data",
            "Delete folder Backup",
            "Erase directory temp_files",
            "Delete the folder structure for projects"
        ]
    },
    {
        "tool_name": "rename_folder",
        "description": "Rename an existing folder.",
        "examples": [
            "Rename folder AI Projects to Machine Learning",
            "Change directory name from Work to Job",
            "Rename folder Resume to CV",
            "Change name of directory downloads to files",
            "Rename folder projects to workspace",
            "Rename the folder temp to cache",
            "Rename directory logs to system_logs",
            "Change folder name of test to validation"
        ]
    },

    # ----------------------------------------------------
    # Category: Notepad / File Operations (3 tools)
    # ----------------------------------------------------
    {
        "tool_name": "open_notepad_and_write",
        "description": "Open Notepad and write specified text.",
        "examples": [
            "Open Notepad and write hello world",
            "Launch Notepad and type meeting notes",
            "Start Notepad and write hey there",
            "Open text editor and type shopping list"
        ]
    },
    {
        "tool_name": "append_to_file",
        "description": "Append text to the end of a file.",
        "examples": [
            "Append hello to notes.txt",
            "Add this line to todo.txt",
            "Write some more text to report.txt",
            "Append meeting notes to notes.txt",
            "Add 'done' to the end of task.log",
            "Append text to my document file",
            "Insert some new lines at the end of log.txt",
            "Append text content to data.txt"
        ]
    },
    {
        "tool_name": "read_file_content",
        "description": "Read and return the text content of a file.",
        "examples": [
            "Read notes.txt",
            "Show contents of report.docx",
            "What is inside todo.txt?",
            "Display the text file content",
            "Read the contents of info.log",
            "Open and read config.json",
            "What does data.txt say?",
            "Print text contents of summary.txt"
        ]
    },

    # ----------------------------------------------------
    # Category: Screenshot & OCR (2 tools)
    # ----------------------------------------------------
    {
        "tool_name": "take_screenshot",
        "description": "Capture a screenshot of the screen.",
        "examples": [
            "Take a screenshot",
            "Capture the screen",
            "Take a snapshot",
            "Save a screenshot"
        ]
    },
    {
        "tool_name": "extract_text_from_image",
        "description": "Extract text from an image using OCR.",
        "examples": [
            "Extract text from screenshot.png",
            "OCR this image",
            "Get text from scan.jpg",
            "Read words from the picture",
            "Do OCR on invoice_scan.png",
            "Extract words from photo.jpg",
            "Scan image file.png and retrieve text",
            "Get textual content from this screenshot"
        ]
    },

    # ----------------------------------------------------
    # Category: Advanced File Search (4 tools)
    # ----------------------------------------------------
    {
        "tool_name": "semantic_file_search",
        "description": "Search for files using semantic meaning of the content or filename.",
        "examples": [
            "Semantically search for files about AI",
            "Find documents relating to machine learning",
            "Search files containing project details",
            "Find files about finance",
            "Look for articles discussing neural networks",
            "Find papers on semantic search",
            "Search files related to user specifications",
            "Find documents describing system requirements"
        ]
    },
    {
        "tool_name": "recent_files",
        "description": "List recently accessed or modified files.",
        "examples": [
            "Show my recent files",
            "What files did I open recently?",
            "List recent documents",
            "Show what I worked on today",
            "Give me list of files modified recently",
            "Show active file history",
            "What were the last files I accessed?",
            "List files changed in the last 24 hours"
        ]
    },
    {
        "tool_name": "files_by_extension",
        "description": "Filter and list files by their file extension.",
        "examples": [
            "Find all PDF files",
            "List text documents with txt extension",
            "Show me my py files",
            "Find python files",
            "Show all word documents docx in folder",
            "List jpg files on my computer",
            "Find all zip archives",
            "Filter files by extension json"
        ]
    },
    {
        "tool_name": "files_by_date",
        "description": "Filter and list files by their creation or modification date.",
        "examples": [
            "Find files modified yesterday",
            "List documents from last week",
            "Show files created in 2026",
            "Find files by date",
            "Filter documents modified on May 5th",
            "Show files written in the last month",
            "Search files created today",
            "List items updated this year"
        ]
    },

    # ----------------------------------------------------
    # Category: Web & Browser Control (5 tools)
    # ----------------------------------------------------
    {
        "tool_name": "open_website",
        "description": "Open a specific website URL in the browser.",
        "examples": [
            "Open google.com",
            "Go to github.com",
            "Open YouTube website",
            "Launch website wikipedia.org",
            "Open URL stackoverflow.com",
            "Navigate to reddit.com",
            "Go to the website news.ycombinator.com",
            "Open yahoo website"
        ]
    },
    {
        "tool_name": "close_browser",
        "description": "Close the web browser application.",
        "examples": [
            "Close browser",
            "Exit Chrome browser",
            "Close the web browser window",
            "Shut down browser",
            "Close Microsoft Edge browser",
            "Terminate web browser application",
            "Quit browser window",
            "Kill web browser process"
        ]
    },
    {
        "tool_name": "open_new_tab",
        "description": "Open a new blank tab in the active browser window.",
        "examples": [
            "Open a new tab",
            "Make a new browser tab",
            "Launch tab",
            "Create new tab",
            "Open a fresh tab in browser",
            "Start a new blank tab",
            "Open tab in active window",
            "Open empty tab"
        ]
    },
    {
        "tool_name": "switch_tab",
        "description": "Switch to a specific tab in the browser.",
        "examples": [
            "Switch to next tab",
            "Go to tab google.com",
            "Switch browser tab",
            "Focus github tab",
            "Change browser tabs",
            "Move to the tab with YouTube",
            "Switch active tab to Wikipedia",
            "Go to tab number 3"
        ]
    },
    {
        "tool_name": "close_tab",
        "description": "Close the active or a specific tab in the browser.",
        "examples": [
            "Close current tab",
            "Close this browser tab",
            "Shut the tab",
            "Close active web tab",
            "Close tab containing google.com",
            "Close the current browser tab window",
            "Shut the github tab",
            "Close this tab"
        ]
    },

    # ----------------------------------------------------
    # Category: Web Search (3 tools)
    # ----------------------------------------------------
    {
        "tool_name": "google_search",
        "description": "Perform a search query on Google.",
        "examples": [
            "Search Google for weather",
            "Google python tutorials",
            "Look up machine learning on Google",
            "Google search how to write python",
            "Search for standard model of physics on Google",
            "Google search local restaurants",
            "Perform google search for news today",
            "Look up on Google: how to install faiss"
        ]
    },
    {
        "tool_name": "youtube_search",
        "description": "Search for a video or query on YouTube.",
        "examples": [
            "Search YouTube for cat videos",
            "YouTube search python programming",
            "Find tutorial on YouTube",
            "Look up cooking videos on YouTube",
            "Search YouTube for piano tutorials",
            "YouTube search mechanical keyboard review",
            "Find music video on YouTube",
            "Search for gaming clips on YouTube"
        ]
    },
    {
        "tool_name": "website_search",
        "description": "Search for information within a specific website.",
        "examples": [
            "Search wikipedia for AI",
            "Search github for python repos",
            "Search stackoverflow for how to fix error",
            "Search documentation on python.org for lists",
            "Search on medium.com for machine learning articles",
            "Search docs on reactjs.org for hooks",
            "Search inside amazon.com for mechanical keyboard",
            "Search on reddit for nvidia driver bugs"
        ]
    },

    # ----------------------------------------------------
    # Category: Web Form Interactions (2 tools)
    # ----------------------------------------------------
    {
        "tool_name": "fill_form",
        "description": "Fill form fields on a webpage.",
        "examples": [
            "Fill in the email input",
            "Enter text in the username field",
            "Fill form details",
            "Write my address in the form input field",
            "Type my phone number in the form text box",
            "Fill search query inside search box",
            "Enter comments in the feedback area",
            "Fill out the login form fields"
        ]
    },
    {
        "tool_name": "submit_form",
        "description": "Submit a form on a webpage.",
        "examples": [
            "Submit the form",
            "Click submit button",
            "Send form details",
            "Press enter on form",
            "Submit registration details",
            "Click on the form submit link",
            "Submit login form",
            "Send feedback form"
        ]
    },

    # ----------------------------------------------------
    # Category: Page Interactions (3 tools)
    # ----------------------------------------------------
    {
        "tool_name": "click_element",
        "description": "Click a specific element on a webpage.",
        "examples": [
            "Click the login button",
            "Click search icon",
            "Click on the link",
            "Click the button with id submit",
            "Click the download anchor",
            "Click next page button",
            "Click the menu icon",
            "Click the checkbox for terms"
        ]
    },
    {
        "tool_name": "type_text",
        "description": "Type text into an active input or element on a webpage.",
        "examples": [
            "Type hello in search box",
            "Write password in input field",
            "Type query text",
            "Type search terms into search bar",
            "Write message into the chatbox",
            "Type username in text area",
            "Write code sample in compiler webpage",
            "Type input text value"
        ]
    },
    {
        "tool_name": "scroll_page",
        "description": "Scroll the webpage up, down, or to a specific element.",
        "examples": [
            "Scroll down the page",
            "Scroll up",
            "Scroll to bottom",
            "Scroll to submit button",
            "Scroll down by 500 pixels",
            "Scroll to the top of the browser",
            "Scroll to element with id footer",
            "Scroll down slightly"
        ]
    },

    # ----------------------------------------------------
    # Category: File Transfer (2 tools)
    # ----------------------------------------------------
    {
        "tool_name": "download_file",
        "description": "Download a file from a URL.",
        "examples": [
            "Download file from example.com/doc.pdf",
            "Download report from link",
            "Get the file from web",
            "Download the pdf from URL",
            "Fetch the installer from web address",
            "Download zip archive from link",
            "Download source code from github release url",
            "Download documentation document from website"
        ]
    },
    {
        "tool_name": "upload_file",
        "description": "Upload a file to a website.",
        "examples": [
            "Upload resume.pdf",
            "Upload photo to profile",
            "Send file to the website",
            "Upload attachment file.docx to form",
            "Submit report.xlsx to upload field",
            "Upload image to the post",
            "Select and upload my files",
            "Send my documents to the page"
        ]
    },

    # ----------------------------------------------------
    # Category: Browser Agent (1 tool)
    # ----------------------------------------------------
    {
        "tool_name": "browser_agent",
        "description": "Launch the browser agent for complex multi-step web tasks.",
        "examples": [
            "Start the browser agent to book a ticket",
            "Run browser agent for web research",
            "Let browser agent handle this page navigation",
            "Open browser agent to find flight tickets",
            "Use browser agent to order food",
            "Run autonomous browser agent to check prices",
            "Launch browser agent to search for active jobs",
            "Trigger browser agent for automated web scraping"
        ]
    }
]
