"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# synk.ai specific schemas

class WaitlistUser(BaseModel):
    """Waitlist signups (collection: waitlistuser)"""
    email: EmailStr
    name: Optional[str] = None
    source: Optional[str] = Field(default="marketing", description="Origin of signup")

class VideoJob(BaseModel):
    """Represents an uploaded video processing job (collection: videojob)"""
    email: Optional[EmailStr] = None
    filename: str
    size_bytes: int
    status: str = Field(default="queued", description="queued|processing|completed|failed")
    progress: int = Field(default=0, ge=0, le=100)
    steps: List[str] = Field(default_factory=lambda: [
        "analyze_content",
        "detect_cuts",
        "auto_captions",
        "select_music",
        "insert_b_roll",
        "color_and_export"
    ])
    current_step: Optional[str] = None
    render_url: Optional[str] = None
    error: Optional[str] = None
