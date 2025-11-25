"""Chat-related Pydantic models."""

from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    thread_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    thread_id: Optional[str] = None
