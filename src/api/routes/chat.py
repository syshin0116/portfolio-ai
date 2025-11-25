"""Chat endpoints."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import json

from src.api.models import ChatRequest, ChatResponse
from src.agent.graph import graph

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint.

    Args:
        request: Chat request with message and optional thread_id

    Returns:
        Chat response with AI reply
    """
    try:
        # Prepare config with thread_id if provided
        config = {}
        if request.thread_id:
            config["configurable"] = {"thread_id": request.thread_id}

        # Invoke the LangGraph agent
        result = await graph.ainvoke(
            {"messages": [{"role": "user", "content": request.message}]},
            config=config
        )

        # Extract the last message from the agent
        messages = result.get("messages", [])
        if not messages:
            raise HTTPException(status_code=500, detail="No response from agent")

        last_message = messages[-1]
        response_text = last_message.get("content", "") if isinstance(last_message, dict) else str(last_message.content)

        return ChatResponse(
            response=response_text,
            thread_id=request.thread_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint.

    Args:
        request: Chat request with message and optional thread_id

    Returns:
        Streaming SSE response with AI reply (compatible with langgraph dev format)
    """
    async def generate() -> AsyncGenerator[str, None]:
        try:
            # Prepare config with thread_id if provided
            config = {}
            if request.thread_id:
                config["configurable"] = {"thread_id": request.thread_id}

            # Stream the LangGraph agent response with messages mode
            async for chunk in graph.astream(
                {"messages": [{"role": "user", "content": request.message}]},
                config=config,
                stream_mode="messages"
            ):
                # chunk is a tuple: (message, metadata)
                # Format: event: messages/partial
                try:
                    message, _ = chunk

                    # Convert message to dict
                    if hasattr(message, "model_dump"):
                        message_data = message.model_dump()
                    elif hasattr(message, "dict"):
                        message_data = message.dict()
                    else:
                        message_data = message

                    # Send in langgraph dev compatible format
                    chunk_json = json.dumps([message_data], ensure_ascii=False, default=repr)
                    yield f"event: messages/partial\ndata: {chunk_json}\n\n"

                except Exception as e:
                    # If serialization fails, send error but continue
                    error_msg = json.dumps({"event": "error", "error": str(e)}, ensure_ascii=False)
                    yield f"event: error\ndata: {error_msg}\n\n"

        except Exception as e:
            error_msg = json.dumps({"error": str(e)}, ensure_ascii=False)
            yield f"event: error\ndata: {error_msg}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
