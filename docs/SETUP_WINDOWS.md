# Windows Setup Guide for Marcus v052

Complete, step-by-step instructions to set up Marcus locally on Windows for development.

---

## Prerequisites

### System Requirements
- Windows 10 or later (64-bit)
- At least 2 GB disk space
- 4 GB RAM minimum (8 GB+ recommended)

### Required Software
- **Python 3.12** (with pip)
- **Git** (for cloning/versioning)
- **PowerShell 5.1** (built-in on Windows 10+)
- **Ollama** (optional, for chat features)

---

## Step 1: Clone the Repository

```powershell
# Navigate to where you want the code
cd C:\Users\YourUsername\Documents

# Clone the repository
git clone https://github.com/swaggyp52/marcus.git
cd marcus
```

---

## Step 2: Set Up Python Virtual Environment

```powershell
# Navigate to the v052 app folder
cd marcus_v052

# Create virtual environment
python -m venv .venv

# Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# You should see (.venv) in your prompt after this

# Upgrade pip to latest
python -m pip install --upgrade pip
```

**If you get a permission error on Activate.ps1:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# Then try again
.\.venv\Scripts\Activate.ps1
```

---

## Step 3: Install Python Dependencies

```powershell
# Make sure you're in marcus_v052/ with venv activated
pip install -r requirements.txt
```

**This installs**:
- `fastapi` - REST framework
- `uvicorn` - Web server
- `sqlmodel` - Database ORM
- `pywebview` - Desktop GUI
- `pyinstaller` - EXE bundler
- Plus transitive dependencies

**Expected output**: ~50-100 packages installed, takes 2-3 minutes

---

## Step 4: Verify Python Installation

```powershell
# Check Python version
python --version
# Should output: Python 3.12.x

# Check FastAPI import (verify install worked)
python -c "import fastapi; print(fastapi.__version__)"
# Should output: 0.109.0
```

---

## Step 5: (Optional) Install Ollama for Chat

If you want the chat feature to work:

1. Download Ollama from: https://ollama.ai
2. Install and run (default port: 11434)
3. Pull a model: `ollama pull llama2`
4. Leave Ollama running in the background

**Without Ollama**: Chat endpoint returns stub responses, app still works

---

## Step 6: Quick Test - Start Backend Locally

```powershell
# Make sure venv is still active (.venv in prompt)
cd marcus_v052

# Start the FastAPI dev server
python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload
```

**Expected output**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Test it**:
```powershell
# Open a NEW PowerShell window and run:
Invoke-WebRequest http://127.0.0.1:8000/health -UseBasicParsing | Select-Object StatusCode, Content

# Should output:
# StatusCode: 200
# Content: {"status":"ok",...}
```

**Stop the server**: Press `Ctrl+C` in the first terminal

---

## Step 7: Build the Windows Executable

```powershell
# Make sure venv is active
# Navigate to root of marcus repo
cd C:\Users\YourUsername\Documents\marcus

# Run full build pipeline
powershell -ExecutionPolicy Bypass -File marcus_v052\scripts\do_v052_all.ps1
```

**What this does**:
1. Validates environment ✓
2. Installs dependencies ✓
3. Compiles Python backend ✓
4. Runs smoke test on backend ✓
5. Bundles with PyInstaller → `Marcus_v052.exe` ✓
6. Runs integration tests ✓

**Expected time**: 5-7 minutes

**Output**: `marcus_v052\dist\Marcus_v052.exe` (~31.5 MB)

---

## Step 8: Launch the App

```powershell
# Run the EXE
.\marcus_v052\dist\Marcus_v052.exe
```

**What you should see**:
- A desktop window appears with the Marcus logo
- Status indicator shows "Online"
- Upload area visible
- Chat interface on the right
- Knowledge graph on the left

**First launch**: Backend starts, database initializes (~3-5 seconds)

---

## Step 9: Test the App

### Upload a Document
1. Click "Add Documents" or drag a .txt/.pdf file
2. See progress bar
3. Document appears in grid

### Chat
1. Click hint button like "What is this?"
2. Type a question, press Enter
3. Marcus responds (if Ollama running, real response; otherwise stub)

### Knowledge Graph
1. Left sidebar shows uploaded documents
2. Statistics: X documents, Y concepts, Z connections
3. Canvas visualization (if documents processed)

---

## Step 10: Development Workflow

### Edit Backend
```powershell
# Terminal 1: Start dev server with auto-reload
cd marcus_v052
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.api:app --reload

# Terminal 2: Edit backend/api.py, save, server auto-reloads
# Test changes at http://localhost:8000/health
```

### Edit Frontend
```powershell
# While backend is running from above
# Edit marcus_v052/frontend/index.html, style.css, app.js
# Refresh browser to see changes (no build step needed)

# Access at: http://localhost:8000/ or use app's browser
```

### Run Quality Checks
```powershell
cd C:\Users\YourUsername\Documents\marcus
powershell -ExecutionPolicy Bypass -File scripts\quality.ps1
```

**Checks**: Python syntax, build success, integration tests

---

## Step 11: Next Steps

### To Add a Feature
1. Edit backend code (`backend/api.py`, `backend/models.py`)
2. Edit frontend code (`frontend/*.js`, `frontend/*.css`)
3. Test locally with `python -m uvicorn ...`
4. Rebuild: `.\marcus_v052\scripts\do_v052_all.ps1`

### To Debug
1. Use browser DevTools (F12)
2. Check console for JS errors
3. Check backend logs (terminal output from uvicorn)

### To Run Tests
```powershell
# (If tests added in future)
cd marcus_v052
.\.venv\Scripts\pytest
```

### To Install More Packages
```powershell
# Activate venv
.\.venv\Scripts\Activate.ps1

# Install package
pip install package-name

# Add to requirements.txt
echo "package-name==1.2.3" >> requirements.txt

# Test, then rebuild
.\scripts\do_v052_all.ps1
```

---

## Troubleshooting

### "Python not found"
```powershell
# Ensure Python 3.12 is in PATH
python --version

# If not found, add Python to PATH or reinstall
# https://www.python.org/downloads/
```

### "venv activation fails"
```powershell
# Try with absolute path
C:\Users\YourUsername\marcus\marcus_v052\.venv\Scripts\Activate.ps1

# Or set execution policy first
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\.venv\Scripts\Activate.ps1
```

### "Port 8000 already in use"
```powershell
# Kill existing process
Stop-Process -Name Marcus_v052 -Force -ErrorAction SilentlyContinue

# Or specify different port
python -m uvicorn backend.api:app --port 8001 --reload
```

### "ModuleNotFoundError: No module named fastapi"
```powershell
# Venv not activated, or pip install failed
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### "PyInstaller fails"
```powershell
# Ensure pyinstaller is installed
pip install pyinstaller

# Then retry
.\marcus_v052\scripts\build_windows_exe.ps1
```

### "EXE won't start"
```powershell
# Check event viewer for errors
# Or run debug version
cd marcus_v052
python launcher.py

# This shows errors in console
```

### "Chat not responding"
```powershell
# Check if Ollama is running
netstat -ano | Select-String "11434"

# Or start Ollama
# https://ollama.ai
```

---

## File Locations Quick Ref

```
Repo root:          C:\Users\YourUsername\Documents\marcus\
App code:           C:\Users\YourUsername\Documents\marcus\marcus_v052\
Backend:            C:\Users\YourUsername\Documents\marcus\marcus_v052\backend\
Frontend:           C:\Users\YourUsername\Documents\marcus\marcus_v052\frontend\
Build scripts:      C:\Users\YourUsername\Documents\marcus\marcus_v052\scripts\
Built EXE:          C:\Users\YourUsername\Documents\marcus\marcus_v052\dist\Marcus_v052.exe
Database (runtime): C:\Users\YourUsername\Documents\marcus\marcus_v052\data\marcus_v052.db
```

---

## One-Command Summary

```powershell
# Full setup (run from repo root after cloning)
cd marcus
cd marcus_v052
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..
powershell -ExecutionPolicy Bypass -File marcus_v052\scripts\do_v052_all.ps1
.\marcus_v052\dist\Marcus_v052.exe
```

---

## Support

If you hit issues:
1. Check [ENTRYPOINTS.md](ENTRYPOINTS.md) for quick reference commands
2. Check [DEPENDENCIES.md](DEPENDENCIES.md) for version compatibility
3. Review console output for error messages
4. Check [REPO_MAP.md](REPO_MAP.md) to understand folder structure

---

## Next: Development Tooling

Once setup is complete, you can use the **Agent Runner** for automated workflows:

```powershell
# Quality check
powershell -ExecutionPolicy Bypass -File scripts\quality.ps1

# Or run specific agent (when available)
powershell -ExecutionPolicy Bypass -File scripts\agent.ps1 builddoctor
```

See [docs/AGENTS.md](AGENTS.md) for details.
