"""LangGraph Server API compatible runs endpoints."""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from src.api.models import RunsStreamRequest, RagMode
from src.agent.graph import get_agent
from src.core.streaming import generate_multi_agent_stream
from src.core.logger import get_logger, log_request, log_response

router = APIRouter()
logger = get_logger(__name__)


@router.post("/runs/stream")
async def runs_stream(request: RunsStreamRequest):
    """LangGraph Server API compatible runs/stream endpoint (stateless).

    This endpoint mimics the LangGraph Server API format, allowing clients
    to use @langchain/langgraph-sdk directly.

    Args:
        request: Run request with assistant_id, input, config, stream_mode

    Returns:
        SSE stream compatible with LangGraph Server API format
    """
    log_request(logger, "/runs/stream", {
        "assistant_id": request.assistant_id,
        "input": request.input,
        "config": request.config,
        "stream_mode": request.stream_mode,
        "rag_modes": request.rag_modes
    })

    config = request.config or {}

    # Set default rag_modes if not provided
    rag_modes = request.rag_modes if request.rag_modes else [RagMode.METADATA_SEARCH]
    rag_mode_values = [mode.value for mode in rag_modes]

    # Get independent agents for each RAG mode
    agents = [get_agent(mode) for mode in rag_mode_values]

    # Add rag_modes to config
    if "configurable" not in config:
        config["configurable"] = {}
    config["configurable"]["rag_modes"] = rag_mode_values

    response = StreamingResponse(
        generate_multi_agent_stream(
            agents=agents,
            rag_modes=rag_mode_values,
            input_data=request.input,
            config=config,
            stream_mode=request.stream_mode,
            assistant_id=request.assistant_id
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

    log_response(logger, "/runs/stream")
    return response
