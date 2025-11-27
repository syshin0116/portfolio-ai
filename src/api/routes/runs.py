"""LangGraph Server API compatible runs endpoints."""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from src.api.models import RunsStreamRequest
from src.agent.graph import graph
from src.core.streaming import generate_langgraph_stream
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
        "stream_mode": request.stream_mode
    })

    config = request.config or {}

    response = StreamingResponse(
        generate_langgraph_stream(
            graph=graph,
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
