"""FastAPI application for Marcus."""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from typing import List
from pathlib import Path
import sys
import os

from backend.models import Item, AppSettings
from backend.database import init_db, get_session

# Create FastAPI app
app = FastAPI(title="Marcus", version="0.5.2")

# Initialize database on startup
@app.on_event("startup")
def on_startup():
    init_db()


# Determine frontend path
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    FRONTEND_PATH = Path(sys._MEIPASS) / 'frontend'
else:
    # Running as script
    FRONTEND_PATH = Path(__file__).parent.parent / 'frontend'


# API Routes
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.5.2"}


@app.get("/api/items", response_model=List[Item])
async def get_items(session: Session = Depends(get_session)):
    """Get all items."""
    items = session.exec(select(Item)).all()
    return items


@app.post("/api/items", response_model=Item)
async def create_item(item: Item, session: Session = Depends(get_session)):
    """Create a new item."""
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@app.get("/api/items/{item_id}", response_model=Item)
async def get_item(item_id: int, session: Session = Depends(get_session)):
    """Get a specific item by ID."""
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.put("/api/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item: Item, session: Session = Depends(get_session)):
    """Update an item."""
    db_item = session.get(Item, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item_data = item.dict(exclude_unset=True, exclude={"id"})
    for key, value in item_data.items():
        setattr(db_item, key, value)
    
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


@app.delete("/api/items/{item_id}")
async def delete_item(item_id: int, session: Session = Depends(get_session)):
    """Delete an item."""
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    session.delete(item)
    session.commit()
    return {"message": "Item deleted successfully"}


# Static files and frontend
if FRONTEND_PATH.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_PATH / "static")), name="static")

    @app.get("/")
    async def serve_frontend():
        """Serve the frontend HTML."""
        return FileResponse(str(FRONTEND_PATH / "index.html"))
else:
    @app.get("/")
    async def serve_frontend():
        """Fallback when frontend is not available."""
        return {"message": "Marcus API is running", "version": "0.5.2"}
