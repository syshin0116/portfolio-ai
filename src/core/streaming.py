"""Streaming utilities for LangGraph Server API compatibility."""

import json
import uuid
from datetime import datetime
from typing import AsyncGenerator, Dict, Any

from src.core.logger import get_logger, log_step, log_error

logger = get_logger(__name__)


async def generate_langgraph_stream(
    graph,
    input_data: Dict[str, Any],
    config: Dict[str, Any],
    stream_mode: str,
    assistant_id: str = "agent"
) -> AsyncGenerator[str, None]:
    """Generate SSE stream in LangGraph Server API format.

    Args:
        graph: LangGraph compiled graph
        input_data: Input data for the graph
        config: Configuration for the graph execution
        stream_mode: Stream mode (messages, values, updates, etc.)
        assistant_id: Assistant ID for metadata

    Yields:
        SSE formatted strings
    """
    try:
        # Generate run_id and get/create thread_id
        run_id = str(uuid.uuid4())
        thread_id = config.get("configurable", {}).get("thread_id") or str(uuid.uuid4())
        event_counter = 0

        log_step(logger, "Starting stream", f"run_id={run_id}, thread_id={thread_id}")
        logger.debug(f"Input: {json.dumps(input_data, ensure_ascii=False, default=str)[:200]}...")
        logger.debug(f"Config: {json.dumps(config, ensure_ascii=False, default=str)}")

        # Ensure thread_id is in config for checkpointer
        if "configurable" not in config:
            config["configurable"] = {}
        config["configurable"]["thread_id"] = thread_id

        # Send metadata event
        metadata = {
            "run_id": run_id,
            "thread_id": thread_id,
            "attempt": 1
        }
        yield f"event: metadata\ndata: {json.dumps(metadata, ensure_ascii=False)}\nid: {int(datetime.now().timestamp() * 1000)}-{event_counter}\n\n"
        event_counter += 1

        # Stream the LangGraph agent response
        log_step(logger, "Streaming graph output", f"stream_mode={stream_mode}")
        async for chunk in graph.astream(
            input_data,
            config=config,
            stream_mode=stream_mode
        ):
            try:
                message, metadata = chunk

                # Log message content in pretty format
                if hasattr(message, "content"):
                    logger.debug(f"Message chunk: {message.content}")
                elif hasattr(message, "model_dump"):
                    logger.debug(f"Message chunk: {json.dumps(message.model_dump(), indent=2, ensure_ascii=False)}")
                else:
                    logger.debug(f"Message chunk: {message}")

                log_step(logger, "Processing chunk", f"event_counter={event_counter}")

                # Send messages/metadata event (first chunk only)
                if event_counter == 1:
                    messages_metadata = {
                        f"lc_run--{run_id}": {
                            "metadata": {
                                "run_id": run_id,
                                "thread_id": thread_id,
                                "assistant_id": assistant_id,
                                "langgraph_node": "model",
                            }
                        }
                    }
                    yield f"event: messages/metadata\ndata: {json.dumps(messages_metadata, ensure_ascii=False)}\nid: {int(datetime.now().timestamp() * 1000)}-{event_counter}\n\n"
                    event_counter += 1

                # Convert message to dict
                if hasattr(message, "model_dump"):
                    message_data = message.model_dump()
                elif hasattr(message, "dict"):
                    message_data = message.dict()
                else:
                    message_data = message

                # Send messages/partial event
                chunk_json = json.dumps([message_data], ensure_ascii=False, default=repr)
                yield f"event: messages/partial\ndata: {chunk_json}\nid: {int(datetime.now().timestamp() * 1000)}-{event_counter}\n\n"
                event_counter += 1

            except Exception as e:
                # If serialization fails, send error but continue
                log_error(logger, e, "chunk processing")
                error_msg = json.dumps({"event": "error", "error": str(e)}, ensure_ascii=False)
                yield f"event: error\ndata: {error_msg}\nid: {int(datetime.now().timestamp() * 1000)}-{event_counter}\n\n"
                event_counter += 1

        log_step(logger, "Stream completed", f"total_events={event_counter}")

    except Exception as e:
        log_error(logger, e, "generate_langgraph_stream")
        error_msg = json.dumps({"error": str(e)}, ensure_ascii=False)
        yield f"event: error\ndata: {error_msg}\n\n"
