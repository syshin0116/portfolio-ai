"""LangGraph Server API compatible runs endpoints."""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from src.agent.graph import create_multi_rag_graph
from src.api.models import RagMode, RunsStreamRequest
from src.core.logger import get_logger, log_request, log_response
from src.core.streaming import generate_langgraph_stream

router = APIRouter()
logger = get_logger(__name__)


@router.post("/runs/stream")
async def runs_stream(request: RunsStreamRequest):
    """LangGraph Server API compatible runs/stream endpoint.

    This endpoint creates a dynamic graph with parallel DeepAgent nodes
    based on the selected RAG modes. Each RAG mode runs as an independent
    DeepAgent in parallel, with results streamed as they arrive.

    Architecture:
        START → [metadata_search, filesystem_search, ...] → END
                     (parallel DeepAgents)

    Args:
        request: Run request with assistant_id, input, config, stream_mode, rag_modes

    Returns:
        SSE stream compatible with LangGraph Server API format
    """
    log_request(
        logger,
        "/runs/stream",
        {
            "assistant_id": request.assistant_id,
            "input": request.input,
            "config": request.config,
            "stream_mode": request.stream_mode,
            "rag_modes": request.rag_modes,
        },
    )

    config = request.config or {}

    # Set default rag_modes if not provided
    rag_modes = request.rag_modes if request.rag_modes else [RagMode.METADATA_SEARCH]
    rag_mode_values = [mode.value for mode in rag_modes]

    # Create a single graph with parallel DeepAgent nodes for selected RAG modes
    graph = create_multi_rag_graph(rag_mode_values)

    # Store rag_modes in config for reference (optional, not used by graph)
    if "configurable" not in config:
        config["configurable"] = {}
    config["configurable"]["rag_modes"] = rag_mode_values

    response = StreamingResponse(
        generate_langgraph_stream(
            graph=graph,
            input_data=request.input,
            config=config,
            stream_mode=request.stream_mode,
            assistant_id=request.assistant_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

    log_response(logger, "/runs/stream")
    return response
