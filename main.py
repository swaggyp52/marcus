"""
Marcus v0.5.2 - Main entry point
Desktop application using pywebview and FastAPI
"""
import webview
import threading
import uvicorn
import sys
from pathlib import Path

from backend.api import app


def start_server():
    """Start the FastAPI server in a separate thread."""
    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=8052,
        log_level="info",
        access_log=False
    )
    server = uvicorn.Server(config)
    server.run()


def main():
    """Main entry point for the application."""
    # Start FastAPI server in a separate thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start with health check
    import time
    import requests
    max_retries = 10
    for i in range(max_retries):
        try:
            requests.get('http://127.0.0.1:8052/api/health', timeout=1)
            break
        except:
            if i < max_retries - 1:
                time.sleep(0.5)
            else:
                print("Warning: Server may not have started properly")
    
    # Create and start the webview window
    window = webview.create_window(
        title='Marcus v0.5.2',
        url='http://127.0.0.1:8052',
        width=1400,
        height=900,
        resizable=True,
        fullscreen=False,
        min_size=(800, 600)
    )
    
    webview.start(debug=False)


if __name__ == '__main__':
    main()
