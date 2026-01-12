# Marcus v052 — Life Globe

FastAPI + PyInstaller Windows desktop app with a neon 2D canvas globe UI, SQLModel/SQLite backend, and automation scripts for build/smoke-test. Ollama adapter included for local LLM parsing/planning when available.

## Quick start (dev)

1) Create virtualenv (optional):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) Run backend (dev):
```powershell
python -m uvicorn backend.api:app --reload --host 127.0.0.1 --port 8000
# open http://127.0.0.1:8000
```

## Build EXE (Windows)
```powershell
.\scripts\build_windows_exe.ps1
```

## Smoke test the EXE
```powershell
.\scripts\smoke_test.ps1
```

## Notes
- Frontend is vanilla ES modules + canvas neon globe (2D fallback). Three.js globe can be added later.
- Ollama adapter is included; if Ollama runs locally, chat will use it for parsing/planning.
