# Aether — Offline AI Desktop Assistant

Aether is a privacy-first, offline AI Desktop Assistant built using a Python FastAPI backend and a React/TypeScript frontend. It integrates local GGUF models via `llama-server` to orchestrate multi-step desktop actions (file management, browser control, application launching, system volume/brightness, and automated text input).

---

## 📋 Prerequisites

Before running Aether, ensure you have the following installed on your system:
* **Python 3.10 or 3.11** (recommended version)
* **Node.js** (v18+) and **pnpm** (or npm/yarn)
* **GGUF Models**:
  * **Router Model**: `qwen2.5-3b-instruct-q4_k_m.gguf` (approx. 3B parameters)
  * **Planner Model**: `qwen2.5-coder-7b-instruct-q4_k_m.gguf` (approx. 7B parameters)

---

## 📂 Model Setup & Directory Structure

Place your GGUF models inside the models folder so Aether can auto-detect them:

```
aether/
    models/
        gguf/
            qwen2.5-3b-instruct-q4_k_m.gguf
            qwen2.5-coder-7b-instruct-q4_k_m.gguf
```

> [!TIP]
> **Downloads Folder Fallback**: On first-run, if the `aether/models/gguf/` directory is empty, Aether will check your standard user `Downloads` directory for these filenames as a fallback.

---

## 🚀 Running the Application

Setting up Aether requires launching both the **Backend API server** and the **Frontend dev interface**.

### 1. Backend Setup (FastAPI & LLM Sidecars)

1. Navigate to the project root directory.
2. Initialize and activate a Python virtual environment:
   * **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   * **macOS / Linux**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the backend application:
   ```bash
   python aether/web_main.py
   ```
   * *This will scan your models folder, check the active `config.json` selection, launch the backend server on `http://127.0.0.1:8000`, and start the background `llama-server` sidecar processes.*

---

### 2. Frontend Setup (React & Vite)

1. Open a new terminal tab/window.
2. Navigate to the `frontend` folder:
   ```bash
   cd frontend
   ```
3. Install frontend dependencies:
   ```bash
   pnpm install
   # or: npm install
   ```
4. Run the Vite development server:
   ```bash
   pnpm dev
   # or: npm run dev
   ```
5. Open your web browser and navigate to the address shown in the console (typically `http://localhost:5173`).

---

## ⚙️ Platform-Specific Settings

Aether utilizes a modular platforms layer (`aether/platforms/`) to ensure feature parity across operating systems.

### 💻 Windows
* Native integrations use standard Win32 DLLs and Registry queries.
* Runs immediately out-of-the-box.

### 🍎 macOS
To allow Aether to control applications, type text, and resize windows, macOS requires system authorization:
1. **Accessibility**: When Aether first attempts to focus window groups or type text, macOS will prompt you to grant the calling application (terminal/IDE/Python) Accessibility privileges. You can also add it manually under *System Settings ➔ Privacy & Security ➔ Accessibility*.
2. **Screen Recording**: Required for taking screenshots (`screencapture` tool). Grant access under *System Settings ➔ Privacy & Security ➔ Screen Recording*.
3. **Automation**: Allow the Python process to control System Events and target browsers (Safari / Google Chrome).
