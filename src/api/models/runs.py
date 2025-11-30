"""LangGraph Server API compatible models."""

from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from enum import Enum


class RagMode(str, Enum):
    """Available RAG modes for blog search."""
    METADATA_SEARCH = "metadata_search"
    FILESYSTEM_SEARCH = "filesystem_search"
    VECTOR_SEARCH = "vector_search"
    GRAPH_SEARCH = "graph_search"


class RunsStreamRequest(BaseModel):
    """LangGraph Server compatible runs/stream request."""
    assistant_id: str = "agent"
    input: Dict[str, Any]
    config: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    stream_mode: str = "messages"  # Can be "messages", "values", "updates", etc.
    rag_modes: Optional[List[RagMode]] = None  # RAG modes (default: metadata_search if None)
