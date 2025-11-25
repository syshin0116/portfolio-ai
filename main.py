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
        Streaming SSE response with AI reply
    """
    async def generate() -> AsyncGenerator[str, None]:
        try:
            # Prepare config with thread_id if provided
            config = {}
            if request.thread_id:
                config["configurable"] = {"thread_id": request.thread_id}

            # Stream the LangGraph agent response
            async for event in graph.astream_events(
                {"messages": [{"role": "user", "content": request.message}]},
                config=config,
                version="v2"
            ):
                # Filter for LLM token events
                if event["event"] == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        # Send SSE format
                        yield f"data: {json.dumps({'content': content})}\n\n"

            # Send completion signal
            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

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
