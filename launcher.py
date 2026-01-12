import subprocess, sys, time, webbrowser, os, threading
from pathlib import Path

BASE = Path(__file__).parent
PY = sys.executable
IS_FROZEN = getattr(sys, 'frozen', False)

# Ensure backend module can be found
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

def start_backend_subprocess():
    """Start backend as subprocess (development mode)"""
    port = os.environ.get('MARCUS_PORT', '8000')
    env = os.environ.copy()
    env['PYTHONPATH'] = str(BASE)
    proc = subprocess.Popen(
        [PY, "-m", "uvicorn", "backend.api:app", "--host", "127.0.0.1", "--port", port],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(BASE),
        env=env
    )
    return proc

def start_backend_thread():
    """Start backend in a thread (frozen/bundled mode)"""
    import uvicorn
    from backend.api import app
    port = int(os.environ.get('MARCUS_PORT', '8000'))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

def start_backend():
    """Start backend - subprocess if development, thread if frozen"""
    if IS_FROZEN:
        # Bundled EXE: run in thread
        thread = threading.Thread(target=start_backend_thread, daemon=True)
        thread.start()
        return thread
    else:
        # Development: run as subprocess
        return start_backend_subprocess()

if __name__=='__main__':
    proc = start_backend()
    # wait for /health
    import requests
    port = os.environ.get('MARCUS_PORT', '8000')
    url = f'http://127.0.0.1:{port}/health'
    for i in range(30):
        try:
            r = requests.get(url, timeout=1)
            if r.status_code==200:
                break
        except Exception:
            pass
        time.sleep(0.5)
    
    # open browser unless headless mode
    if not os.environ.get('MARCUS_HEADLESS'):
        webbrowser.open(f'http://127.0.0.1:{port}')
    
    try:
        if IS_FROZEN:
            # Thread will run in background
            while True:
                time.sleep(1)
        else:
            # Subprocess: wait for it
            proc.wait()
    except KeyboardInterrupt:
        if not IS_FROZEN and proc:
            proc.terminate()
