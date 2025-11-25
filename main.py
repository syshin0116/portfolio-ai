"""FastAPI production server for Portfolio AI.

This wraps the LangGraph agent for production deployment.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, AsyncGenerator
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the LangGraph agent
from src.agent.graph import graph

app = FastAPI(
    title="Portfolio AI",
    description="AI assistant for Syshin's portfolio",
    version="0.0.1",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    thread_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    thread_id: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Portfolio AI",
        "status": "running",
        "version": "0.0.1"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
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


@app.post("/chat/stream")
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


@app.get("/info")
async def info():
    """Get agent information."""
    return {
        "agent": "Portfolio AI",
        "capabilities": [
            "Search blog posts",
            "Get blog content",
            "Answer questions about portfolio"
        ],
        "tools": ["search_blog_summaries", "get_blog_content"]
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
