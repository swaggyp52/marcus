# Marcus v052 Entrypoints & How to Run

Quick reference for running the app, backend, frontend, and build commands.

---

## 1. Running the Finished App (Users)

### Windows Desktop (Recommended)
```powershell
# Double-click or run:
.\marcus_v052\dist\Marcus_v052.exe

# Or from command line:
Start-Process -FilePath ".\marcus_v052\dist\Marcus_v052.exe"
```

**What happens**:
1. Python backend starts on `http://localhost:8000`
2. PyWebView opens a desktop window pointing to the backend
3. Frontend loads (HTML/CSS/JS)
4. User can upload documents, chat with Marcus, view knowledge graph

**Data stored**: `marcus_v052\data\marcus_v052.db` + uploaded files in `data\files\`

---

## 2. Building from Source (Developers)

### Full Pipeline (Build + Test)
```powershell
cd C:\Users\conno\marcus
powershell -ExecutionPolicy Bypass -File marcus_v052\scripts\do_v052_all.ps1
```

**What it does**:
1. ✓ Validates Python environment
2. ✓ Installs dependencies (pip install -r requirements.txt)
3. ✓ Compiles Python backend (syntax check)
4. ✓ Runs smoke test on backend
5. ✓ Bundles with PyInstaller → `dist\Marcus_v052.exe`
6. ✓ Runs integration smoke test (health, graph, chat endpoints)
7. ✓ Packages ZIP for distribution

**Output**: 
- `marcus_v052\dist\Marcus_v052.exe` (~31.5 MB)
- Build logs in console

**Time**: ~5-7 minutes

### Build Only (Skip Testing)
```powershell
powershell -ExecutionPolicy Bypass -File marcus_v052\scripts\build_windows_exe.ps1
```

**Faster, but no verification.**

---

## 3. Local Development (Backend)

### Start Backend Server (Manual)
```powershell
cd marcus_v052

# Activate venv (if not already)
.\.venv\Scripts\Activate.ps1

# Start FastAPI dev server
python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload
```

**What you see**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Hot reload**: Edits to `backend/api.py` auto-reload (no restart needed)

**Access**:
- API: `http://localhost:8000/health` → `{"status": "ok", ...}`
- Frontend: `http://localhost:8000/` → loads index.html

### Health Check
```powershell
Invoke-WebRequest http://127.0.0.1:8000/health -UseBasicParsing
```

---

## 4. Local Development (Frontend)

### Hot-Reload Frontend Code
The frontend files (`index.html`, `style.css`, `app.js`) are served as static files.

**Option A**: Edit while backend is running
```powershell
# Terminal 1: Start backend (see section 3 above)
python -m uvicorn backend.api:app --reload

# Terminal 2: Edit frontend files in your editor
# Changes auto-reload when you refresh the browser
```

**Option B**: Open frontend directly (with limitations)
```powershell
# This works for HTML/CSS testing, but no API calls without backend
start marcus_v052\frontend\index.html
```

### Browser Access (While Backend Running)
```
http://localhost:8000/
```

**Open DevTools**: Press `F12` in browser (if using browser tab) or PyWebView dev tools

### Edit Workflow
1. Edit `marcus_v052/frontend/index.html` (DOM structure)
2. Edit `marcus_v052/frontend/style.css` (styling)
3. Edit `marcus_v052/frontend/app.js` (logic)
4. Refresh browser to see changes

---

## 5. Testing

### Smoke Test (Integration)
```powershell
powershell -ExecutionPolicy Bypass -File marcus_v052\scripts\smoke_test.ps1
```

**Checks**:
- ✓ Backend /health endpoint OK
- ✓ Frontend HTML loads correctly
- ✓ /api/graph endpoint returns valid JSON
- ✓ /api/chat endpoint works
- ✓ Overall integration is solid

**Time**: ~30 seconds

### Python Unit Tests (If Added)
```powershell
cd marcus_v052
.\.venv\Scripts\pytest
```

**Currently**: No unit tests (can be added via agent workflow)

---

## 6. Quality Gates

### Quick Quality Check (Code, Build, Tests)
```powershell
powershell -ExecutionPolicy Bypass -File scripts\quality.ps1
```

**Checks**:
- ✓ Python syntax (compile check)
- ✓ Build can compile (PyInstaller)
- ✓ Integration tests pass (smoke test)
- ✓ Code cleanliness (optional linting)

**Time**: ~2-3 minutes

---

## 7. Data Management

### Database Location
```
marcus_v052\data\marcus_v052.db  (SQLite)
marcus_v052\data\files\          (uploaded documents)
```

### Reset Database (Start Fresh)
```powershell
# WARNING: This deletes all uploaded documents and chat history
Remove-Item marcus_v052\data -Recurse -Force
```

**On next app launch**: Database auto-recreates as empty.

---

## 8. Environment Variables

### Optional Configuration
Create `marcus_v052\.env` (optional) to override defaults:

```
OLLAMA_HOST=http://localhost:11434
MARCUS_PORT=8000
MARCUS_DEBUG=false
```

Currently **not required** (hardcoded defaults work).

---

## 9. Troubleshooting

### "Port 8000 already in use"
```powershell
# Find and kill the process holding port 8000
Get-Process | Where-Object {$_.Id -in @(Get-NetTCPConnection -LocalPort 8000 -ErrorAction Ignore).OwningProcess} | Stop-Process -Force
```

### "ModuleNotFoundError: No module named fastapi"
```powershell
# Ensure venv is active and requirements installed
cd marcus_v052
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### "PyInstaller not found"
```powershell
# Make sure pyinstaller is in requirements.txt and installed
pip install pyinstaller
```

### Frontend not updating after edits
```powershell
# Hard refresh the browser cache
# In browser: Ctrl+Shift+R (or Cmd+Shift+R on Mac)
# Or: Delete-Item marcus_v052\data\* to clear cached files
```

---

## 10. File Locations Quick Reference

```
Source Code:
  Backend:      marcus_v052/backend/
  Frontend:     marcus_v052/frontend/
  Entrypoint:   marcus_v052/launcher.py
  Build Config: marcus_v052/Marcus_v052.spec

Build Artifacts:
  EXE:          marcus_v052/dist/Marcus_v052.exe
  Build temp:   marcus_v052/build/
  Python cache: marcus_v052/__pycache__/

Runtime Data (Created at startup):
  Database:     marcus_v052/data/marcus_v052.db
  Uploads:      marcus_v052/data/files/

Scripts:
  Build:        marcus_v052/scripts/build_windows_exe.ps1
  Full pipeline: marcus_v052/scripts/do_v052_all.ps1
  Test:         marcus_v052/scripts/smoke_test.ps1
  Quality:      scripts/quality.ps1
  Agent runner: scripts/agent.ps1
```

---

## 11. Next Steps

- **To add features**: Edit `backend/api.py` and `frontend/*.js`, rebuild with `do_v052_all.ps1`
- **To debug**: Use `quality.ps1` to verify nothing is broken
- **To investigate issues**: Run `agent.ps1 builddoctor` for diagnostics
- **To document changes**: See `docs/SETUP_WINDOWS.md` for setup instructions

---

## Quick Command Summary

| Task | Command |
|------|---------|
| **Run app** | `.\marcus_v052\dist\Marcus_v052.exe` |
| **Build from source** | `.\marcus_v052\scripts\do_v052_all.ps1` |
| **Start dev backend** | `.\.venv\Scripts\Activate.ps1` then `uvicorn backend.api:app --reload` |
| **Run smoke test** | `.\marcus_v052\scripts\smoke_test.ps1` |
| **Quality check** | `.\scripts\quality.ps1` |
| **Reset data** | `Remove-Item marcus_v052\data -Recurse` |
| **Check health** | `Invoke-WebRequest http://localhost:8000/health` |
