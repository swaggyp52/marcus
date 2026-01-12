"""Database models for Marcus application using SQLModel."""
from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel


class Item(SQLModel, table=True):
    """Sample item model for demonstration."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AppSettings(SQLModel, table=True):
    """Application settings stored in database."""
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True)
    value: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)
