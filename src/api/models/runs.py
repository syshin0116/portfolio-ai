"""LangGraph Server API compatible models."""

from pydantic import BaseModel
from typing import Dict, Any, Optional


class RunsStreamRequest(BaseModel):
    """LangGraph Server compatible runs/stream request."""
    assistant_id: str = "agent"
    input: Dict[str, Any]
    config: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    stream_mode: str = "messages"  # Can be "messages", "values", "updates", etc.
