"""LangGraph Server API compatible models."""

from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel


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
    config: Dict[str, Any] | None = None
    metadata: Dict[str, Any] | None = None
    stream_mode: str = "messages"  # Can be "messages", "values", "updates", etc.
    rag_modes: List[RagMode] | None = (
        None  # RAG modes (default: metadata_search if None)
    )
