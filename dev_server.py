"""
Development server for testing without pywebview
Runs the FastAPI server standalone for development
"""
import uvicorn
from backend.api import app

if __name__ == '__main__':
    print("=" * 50)
    print("Marcus v0.5.2 - Development Server")
    print("=" * 50)
    print("\nStarting FastAPI server...")
    print("Open http://127.0.0.1:8052 in your browser")
    print("Press Ctrl+C to stop\n")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8052,
        log_level="info"
    )
