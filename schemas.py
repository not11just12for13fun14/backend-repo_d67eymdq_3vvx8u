"""
Database Schemas for AlumniConnect

Each Pydantic model represents a collection in your MongoDB database.
Collection name is the lowercase of the class name.

- User -> "user"
- Event -> "event"
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal

class User(BaseModel):
    """
    Users collection schema
    Stores both alumni and students.
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    status: Literal["alumnus", "student"] = Field(..., description="User status")
    batch_year: Optional[int] = Field(None, description="Graduation/Batch year")
    department: Optional[str] = Field(None, description="Department or major")
    current_company: Optional[str] = Field(None, description="Current company (for alumni)")
    designation: Optional[str] = Field(None, description="Job title/designation")
    current_employment: Optional[str] = Field(None, description="Employment status/summary")
    is_active: bool = Field(True, description="Active status")

class Event(BaseModel):
    """
    Events collection schema
    """
    title: str = Field(..., description="Event title")
    date: str = Field(..., description="ISO date string")
    description: Optional[str] = Field(None, description="Event description")
    audience: Optional[str] = Field(None, description="Targeted audience e.g., '2025 batch'")
