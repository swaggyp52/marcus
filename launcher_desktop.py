#!/usr/bin/env python3
"""
Marcus Desktop Launcher
Starts the FastAPI backend, checks mount, and opens pywebview window.
"""

import sys
import subprocess
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
import os
import signal
import threading

# When running as a bundled exe, ensure extracted temp dir is on sys.path
if getattr(sys, 'frozen', False):
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass and meipass not in sys.path:
        sys.path.insert(0, meipass)

# Ensure PyInstaller collects the backend package into the bundle.
try:
    import marcus_app.backend.api
except Exception:
    pass

# Load environment
env_path = Path(__file__).parent / "marcus.env"
load_dotenv(env_path)

# Configuration
BASE_PATH = Path(__file__).parent

# Mount path: use same logic as database.py
# REQUIRED_MOUNT: M:\Marcus (production, VeraCrypt)
# DEV_MOUNT: storage/packaging_temp (testing)

# When bundled as EXE, PyInstaller unpacks to _MEIXXXXX temp dir
# but we look for dev storage in the source directory where the EXE was run from
if getattr(sys, 'frozen', False):
    # Running as bundled EXE
    # The EXE is at: C:\Users\conno\marcus\dist\Marcus.exe (from build script copy)
    # Or it's run from: C:\Users\conno\AppData\Local\Marcus\Marcus.exe (installed location)
    # Either way, look for storage in the original project: C:\Users\conno\marcus\storage\packaging_temp
    # Try current directory first (where EXE is run from), then use absolute project path
    _base_candidates = [
        Path.cwd(),  # Where the EXE is run from
        Path("C:\\Users\\conno\\marcus"),  # Project directory (hardcoded fallback)
    ]
else:
    # Running from source
    _base_candidates = [Path(__file__).parent]

_prod_mount = Path("M:\\Marcus")
_dev_storage = None

# Find dev storage in one of the candidate paths
for _base in _base_candidates:
    _candidate = _base / "storage" / "packaging_temp"
    if _candidate.exists():
        _dev_storage = _candidate
        break

if _prod_mount.exists():
    # Production: use mounted encrypted drive
    ENCRYPTED_MOUNT_PATH = _prod_mount / "storage"
elif _dev_storage:
    # Dev mode: use local test storage
    ENCRYPTED_MOUNT_PATH = _dev_storage
else:
    # Fallback: still require M:\Marcus\ for production
    ENCRYPTED_MOUNT_PATH = _prod_mount / "storage"

API_HOST = "127.0.0.1"
API_PORT = 8000
API_URL = f"http://{API_HOST}:{API_PORT}"
HEALTH_ENDPOINT = f"{API_URL}/health"
MAX_STARTUP_WAIT = 30
HEALTH_CHECK_INTERVAL = 0.5

backend_process = None


def print_header(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_step(step_num, message):
    """Print a numbered step."""
    print(f"\n[{step_num}] {message}")


def check_mount() -> bool:
    """Check if VeraCrypt encrypted storage is mounted.
    Note: The actual mount check is done in database.py.
    We skip it here since dev storage fallback is handled there."""
    print_step(1, "Storage configuration...")
    print(f"  Production mount: {_prod_mount}")
    print(f"  Dev storage: {_dev_storage}")
    print(f"  Using: {ENCRYPTED_MOUNT_PATH}")
    print("[OK] Storage path configured")
    return True


def wait_for_health(timeout: int = MAX_STARTUP_WAIT) -> bool:
    """Poll the /health endpoint until it responds with 200."""
    print_step(2, "Starting Marcus backend...")
    print(f"  Waiting for {HEALTH_ENDPOINT} to respond...")
    print(f"  Timeout: {timeout} seconds")
    
    start_time = time.time()
    attempt = 0
    
    while time.time() - start_time < timeout:
        attempt += 1
        try:
            response = requests.get(HEALTH_ENDPOINT, timeout=2)
            if response.status_code == 200:
                data = response.json()
                print(f"\n  [OK] Backend healthy!")
                print(f"     Status: {data.get('status')}")
                print(f"     Version: {data.get('version')}")
                print(f"     Service: {data.get('service')}")
                return True
        except requests.exceptions.ConnectionError:
            pass
        except requests.exceptions.Timeout:
            pass
        except Exception:
            pass
        
        elapsed = time.time() - start_time
        print(f"  [{elapsed:.1f}s] Attempt {attempt}...", end="\r")
        time.sleep(HEALTH_CHECK_INTERVAL)
    
    print(f"\n  [ERROR] Backend did not respond within {timeout} seconds")
    print(f"     Check logs for errors")
    return False


def start_backend():
    """Start the FastAPI backend using uvicorn."""
    global backend_process
    
    if getattr(sys, 'frozen', False):
        print(f"  Starting embedded uvicorn server in-thread (host={API_HOST} port={API_PORT})")
        try:
            import uvicorn

            def run_uvicorn():
                uvicorn.run("marcus_app.backend.api:app", host=API_HOST, port=API_PORT, log_level="info")

            backend_thread = threading.Thread(target=run_uvicorn, daemon=True)
            backend_thread.start()
            print("  [OK] Embedded backend thread started")
            backend_process = None
            return
        except Exception as e:
            print(f"  [ERROR] Failed to start embedded uvicorn")
            raise

    cmd = [
        sys.executable,
        "-m", "uvicorn",
        "marcus_app.backend.api:app",
        f"--host={API_HOST}",
        f"--port={API_PORT}",
        "--log-level=info"
    ]

    print(f"  Command: {' '.join(cmd)}")
    print(f"  Working directory: {BASE_PATH}")

    backend_process = subprocess.Popen(
        cmd,
        cwd=str(BASE_PATH),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    print(f"  [OK] Backend process started (PID {backend_process.pid})")

    def log_output(pipe, prefix="[BACKEND]"):
        for line in iter(pipe.readline, ''):
            line = line.rstrip()
            if line:
                print(f"  {prefix} {line}")

    if backend_process.stdout:
        threading.Thread(target=log_output, args=(backend_process.stdout,), daemon=True).start()
    if backend_process.stderr:
        threading.Thread(target=log_output, args=(backend_process.stderr, "[BACKEND:ERROR]"), daemon=True).start()


def open_ui_window():
    """Open pywebview window with Marcus UI."""
    print_step(3, "Opening Marcus UI...")
    
    try:
        import webview
    except ImportError:
        print("  [ERROR] pywebview not installed")
        return False
    
    try:
        print(f"  Opening window at {API_URL}")
        print("  Press Ctrl+C to close")
        
        window = webview.create_window(
            title="Marcus - Academic Operating Environment",
            url=API_URL,
            width=1400,
            height=900,
            min_size=(1000, 700)
        )
        
        webview.start()
        return True
        
    except Exception as e:
        print(f"  [ERROR] Failed to open window")
        return False


def cleanup():
    """Gracefully terminate backend process."""
    global backend_process
    
    print_step("cleanup", "Shutting down...")
    
    if backend_process:
        print(f"  Terminating backend (PID {backend_process.pid})...")
        try:
            backend_process.terminate()
            backend_process.wait(timeout=5)
            print("  [OK] Backend stopped")
        except subprocess.TimeoutExpired:
            print("  Force killing backend...")
            backend_process.kill()
            backend_process.wait()
            print("  [OK] Backend force-killed")
    
    print("\n  Marcus closed.")


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n")
    cleanup()
    sys.exit(0)


def main():
    """Main launcher workflow."""
    
    print_header("Marcus Desktop Launcher")
    print(f"\nBase path: {BASE_PATH}")
    print(f"Backend URL: {API_URL}")
    
    signal.signal(signal.SIGINT, signal_handler)
    
    if not check_mount():
        sys.exit(1)
    
    start_backend()
    
    if not wait_for_health():
        cleanup()
        sys.exit(1)
    
    print_step(4, "Launching UI window...")
    try:
        open_ui_window()
    except KeyboardInterrupt:
        pass
    
    cleanup()


if __name__ == "__main__":
    main()
