# Marcus v052 Dependencies

## Runtime (Required to Run)

### Python Packages
```
fastapi==0.109.0              Web framework for REST API
uvicorn[standard]==0.27.0     ASGI server (includes httptools, uvloop)
sqlmodel==0.0.31              ORM + data validation (SQLAlchemy + Pydantic)
sqlalchemy<2.1.0,>=2.0.14     (transitive, via sqlmodel) SQL toolkit
pydantic>=2.7.0               Data validation
requests==2.32.5              HTTP client (for Ollama integration)
python-multipart==0.0.6       Form data parsing (FastAPI uploads)
pywebview==6.1                Desktop GUI wrapper
aiofiles==25.1.0              Async file I/O (FastAPI async uploads)
```

### System-Level
```
Python 3.12.x                 Language runtime
Windows 10/11 (64-bit)        Operating system
```

### Optional (For Ollama integration)
```
Ollama (external service)     LLM inference engine
  - Must be running on localhost:11434 (default)
  - Used by ollama_adapter.py to call models like llama2
```

---

## Build & Development

### Build Tools
```
pyinstaller==6.17.0           EXE bundler (converts Python → Windows .EXE)
pyinstaller-hooks-contrib==2025.11  Auto-detection for common libraries
altgraph==0.17.5              (transitive) dependency graphing
```

### Version Control
```
Git 2.40+                      (external) source control
```

### Testing & Quality
```
pytest>=7.4.3                  Unit testing (if tests added)
python-dotenv==1.0.1          Environment variable loading
```

### Development Scripts (PowerShell)
```
Windows PowerShell 5.1+        Built-in scripting engine
  - Used for build orchestration (build_windows_exe.ps1, etc.)
```

---

## Frontend (Zero External Deps)

**No build step required.**

- HTML5: Native browser APIs
- CSS3: Native browser support (backdrop-filter, @keyframes, grid, flexbox)
- JavaScript: ES6+ (async/await, arrow functions, Fetch API)

**Bundled**: All frontend files (`index.html`, `style.css`, `app.js`) are embedded directly in the Windows EXE via PyInstaller.

---

## Dependency Tree (Simplified)

```
Marcus_v052.exe
 ├─ launcher.py
 │  ├─ pywebview (desktop GUI)
 │  └─ backend.api (FastAPI server)
 │
 └─ backend/api.py (FastAPI)
    ├─ fastapi
    │  └─ starlette
    │     └─ pydantic (validation)
    │
    ├─ uvicorn (ASGI server)
    │
    ├─ sqlmodel (ORM)
    │  └─ sqlalchemy
    │
    ├─ requests (HTTP client)
    │
    ├─ python-multipart (form parsing)
    │
    └─ frontend/ (static files, no runtime deps)
       ├─ index.html
       ├─ style.css
       └─ app.js (vanilla JS, no npm packages)
```

---

## Version Compatibility

| Component | Minimum | Current | Notes |
|-----------|---------|---------|-------|
| Python | 3.10 | 3.12.2 | Type hints, walrus operator |
| FastAPI | 0.100 | 0.109.0 | Pydantic v2 support |
| SQLModel | 0.0.30 | 0.0.31 | Stable ORM |
| PyInstaller | 6.0 | 6.17.0 | Reliable bundling |
| PyWebView | 6.0 | 6.1 | CEF/WebView2 support |

---

## Security Notes

- **No external API calls** (except Ollama, which is optional & local)
- **No telemetry** or tracking
- **No cloud storage**
- **SQLite unencrypted** (all-local database)
- **Frontend assets** served from embedded bundle (no CDN)

---

## Size & Performance

### EXE Size
- **Marcus_v052.exe**: ~31.5 MB
  - Python runtime: ~15 MB
  - FastAPI + deps: ~8 MB
  - PyWebView + CEF: ~6 MB
  - Frontend assets: ~100 KB

### Memory Usage (at runtime)
- Backend process: ~80-120 MB
- Frontend (browser): ~50-100 MB
- Total: ~150-200 MB

### Startup Time
- Cold start: 3-5 seconds
- Warm start: 1-2 seconds

---

## How to Update Dependencies

### Add a new Python package:
```powershell
# 1. Add to requirements.txt
echo "new-package==1.2.3" >> marcus_v052/requirements.txt

# 2. Install locally
.venv\Scripts\pip install -r marcus_v052/requirements.txt

# 3. Test it works, then commit
git add marcus_v052/requirements.txt
git commit -m "Add: new-package for feature X"

# 4. Rebuild EXE (PyInstaller auto-includes)
powershell -ExecutionPolicy Bypass -File marcus_v052/scripts/build_windows_exe.ps1
```

### Remove a package:
```powershell
# Same as above, but remove the line from requirements.txt
```

### Upgrade a package:
```powershell
# Update version in requirements.txt
# Rebuild to test
```

---

## Known Issues & Workarounds

| Issue | Workaround |
|-------|-----------|
| PyInstaller build slow | Normal (~5 min). Use `scripts/do_v052_all.ps1` to parallelize steps. |
| Ollama not found | Install Ollama separately; ensure it runs on :11434 |
| Frontend styles not updating | Clear browser cache in PyWebView dev tools |
| Port 8000 already in use | Kill existing process: `Stop-Process -Name Marcus_v052 -Force` |

---

## Maintenance

- **Check for updates**: `pip list --outdated` (inside .venv)
- **Security**: Monitor PyPI security announcements for fastapi, sqlmodel, pyinstaller
- **Python**: Support for 3.12 ends Oct 2028; plan upgrade by then
