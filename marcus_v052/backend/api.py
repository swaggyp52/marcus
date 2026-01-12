# BugHunter analysis: Issue - patch selftest

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel, Session, create_engine, select
from pathlib import Path
import shutil
import re
import sys
import os
from .models import ClassModel, TaskModel, FileModel
from .ollama_adapter import OllamaAdapter


def get_base_path() -> Path:
    """Get base path for resources (works in both frozen and dev modes)."""
    if getattr(sys, 'frozen', False):
        # PyInstaller sets _MEIPASS when bundled
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass and os.path.exists(os.path.join(meipass, 'frontend')):
            return Path(meipass)
        return Path(sys.executable).parent
    # Dev mode: api.py is in backend/, BASE is parent.parent
    return Path(__file__).parent.parent


BASE: Path = get_base_path()

DATA_DIR = BASE / "data"
FILES_DIR = DATA_DIR / "files"
DB_PATH = DATA_DIR / "marcus_v052.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)
FILES_DIR.mkdir(parents=True, exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

app = FastAPI(title="Marcus v052", version="0.1")

# Mount static frontend
frontend_dir: Path = BASE / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

# create tables
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

ollama = OllamaAdapter()

@app.get("/health")
def health():
    return {"status":"ok","ollama": ollama.is_available()}

@app.get("/")
async def root():
    try:
        index_file = BASE / "frontend" / "index.html"
        if index_file.exists():
            return HTMLResponse(content=index_file.read_text())
        return HTMLResponse(content="<!DOCTYPE html><html><head><title>Marcus v052</title><link rel=\"stylesheet\" href=\"/static/style.css\"></head><body><div id=\"app\"></div><script type=\"module\" src=\"/static/app.js\"></script></body></html>")
    except Exception as e:
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)

@app.get("/api/graph")
def get_graph():
    with Session(engine) as s:
        classes = s.exec(select(ClassModel)).all()
        tasks = s.exec(select(TaskModel)).all()
        files = s.exec(select(FileModel)).all()
    nodes = []
    edges = []
    for c in classes:
        nodes.append({"id": f"class:{c.id}", "type":"class", "label": c.name})
    for t in tasks:
        nodes.append({"id": f"task:{t.id}", "type":"task", "label": t.title, "due": t.due_at.isoformat() if t.due_at else None})
    for f in files:
        nodes.append({"id": f"file:{f.id}", "type":"file", "label": f.filename})
    # simple links: tasks -> classes if title contains class code
    with Session(engine) as s:
        for t in tasks:
            for c in classes:
                if c.code and c.code.lower() in t.title.lower():
                    edges.append({"from": f"task:{t.id}", "to": f"class:{c.id}", "kind":"assignment_of"})
    return {"nodes": nodes, "edges": edges}

# Upload endpoint: save file, extract simple tasks
@app.post("/api/upload")
def upload(file: UploadFile = File(...)):
    dest = FILES_DIR / file.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    text = dest.read_text(errors='ignore')[:20000]
    excerpt = text[:1000]
    # save file record
    fm = FileModel(filename=file.filename, text_excerpt=excerpt, stored_path=str(dest))
    with Session(engine) as s:
        s.add(fm)
        s.commit()
        s.refresh(fm)
    # deterministic extraction: lines with due date keywords
    found = []
    date_re = re.compile(r"(due[:\s]+\w+\s+\d{1,2})|((\d{1,2}/\d{1,2}/\d{2,4}))", re.IGNORECASE)
    for line in text.splitlines():
        if any(k in line.lower() for k in ["due", "deadline", "assign"] ) or date_re.search(line):
            title = line.strip()[:120]
            tm = TaskModel(title=title)
            with Session(engine) as s:
                s.add(tm)
                s.commit()
                s.refresh(tm)
            found.append({"task_id": tm.id, "title": tm.title})
    return {"file_id": fm.id, "excerpt": excerpt[:500], "created_tasks": found}

@app.post("/api/chat")
def chat(payload: dict):
    """Simple agent loop: parse intent, plan, execute small CRUD actions."""
    msg = payload.get('message','')
    context = payload.get('context',{})
    # If Ollama available, ask it to parse plan
    plan_text = None
    if ollama.is_available():
        prompt = f"Parse the user intent and return JSON actions for: {msg}"
        plan_text = ollama.generate(prompt)
    # Fallback deterministic parser
    actions = []
    if plan_text:
        # naive parse: find lines like CREATE_CLASS: name=...,code=...
        for line in plan_text.splitlines():
            if line.strip().upper().startswith('CREATE_CLASS'):
                # naive parse
                parts = line.split(':',1)[1] if ':' in line else ''
                name = parts.split('name=')[-1].split(',')[0].strip() if 'name=' in parts else 'New Class'
                actions.append({'action':'create_class','name': name})
    else:
        if 'create class' in msg.lower():
            # extract class name after 'create class'
            m = re.search(r"create class\s+([\w\s\-]+)", msg, re.IGNORECASE)
            name = m.group(1).strip() if m else 'New Class'
            actions.append({'action':'create_class','name': name})
        if 'create task' in msg.lower() or 'add assignment' in msg.lower():
            m = re.search(r"create task\s+([\w\s\-]+)", msg, re.IGNORECASE)
            title = m.group(1).strip() if m else 'New Task'
            actions.append({'action':'create_task','title': title})
    results = []
    with Session(engine) as s:
        for a in actions:
            if a['action']=='create_class':
                c = ClassModel(name=a.get('name','New Class'))
                s.add(c); s.commit(); s.refresh(c)
                results.append({'created':'class','id':c.id,'name':c.name})
            if a['action']=='create_task':
                t = TaskModel(title=a.get('title','New Task'))
                s.add(t); s.commit(); s.refresh(t)
                results.append({'created':'task','id':t.id,'title':t.title})
    return {"summary":"ok","actions":actions,"results":results}

# simple CRUD for class/task/file
@app.post('/api/class')
def create_class(obj: dict):
    c = ClassModel(**obj)
    with Session(engine) as s:
        s.add(c); s.commit(); s.refresh(c)
    return c

@app.get('/api/classes')
def list_classes():
    with Session(engine) as s:
        return s.exec(select(ClassModel)).all()

@app.get('/api/tasks')
def list_tasks():
    with Session(engine) as s:
        return s.exec(select(TaskModel)).all()

@app.post('/api/link')
def create_link(obj: dict):
    l = Link(**obj)
    with Session(engine) as s:
        s.add(l); s.commit(); s.refresh(l)
    return l
