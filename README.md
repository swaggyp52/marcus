Marcus v052 — Life Globe

Quick start:

1. Create virtualenv (optional):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Run in dev:

```powershell
python -m uvicorn marcus_v052.backend.api:app --reload
# open http://127.0.0.1:8000
```

3. Build EXE (Windows):

```powershell
.\scripts\build_windows_exe.ps1
```

4. Smoke test:

```powershell
.\scripts\smoke_test.ps1
```

Notes:
- The frontend currently uses a neon 2D globe fallback (canvas). Three.js globe can be integrated later.
- Ollama adapter is included; if Ollama is running locally, the chat will use it for parsing/planning.
