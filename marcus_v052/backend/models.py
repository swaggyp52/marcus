from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

class Link(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    from_type: str
    from_id: int
    to_type: str
    to_id: int
    kind: Optional[str] = None

class ClassModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    code: Optional[str] = None
    instructor: Optional[str] = None
    term: Optional[str] = None

class TaskModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    due_at: Optional[datetime] = None
    status: str = "open"

class FileModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    text_excerpt: Optional[str] = None
    stored_path: Optional[str] = None
