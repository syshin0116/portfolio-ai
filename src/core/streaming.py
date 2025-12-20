"""Streaming utilities for LangGraph Server API compatibility."""

import io
import json
import sys
import uuid
from datetime import datetime
from typing import Any, AsyncGenerator, Dict

from src.core.logger import get_logger, log_error, log_step

logger = get_logger(__name__)


def format_message_pretty(message) -> str:
    """Format message object in pretty print style.

    Args:
        message: LangChain message object

    Returns:
        Pretty formatted string
    """
    # Use pretty_repr if available (returns string directly)
    if hasattr(message, "pretty_repr"):
        return message.pretty_repr()

    # Fallback: capture pretty_print output if available
    if hasattr(message, "pretty_print"):
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            message.pretty_print()
            output = sys.stdout.getvalue()
            return output.rstrip()
        finally:
            sys.stdout = old_stdout

    # Final fallback to manual formatting
    if hasattr(message, "__class__"):
        msg_type = message.__class__.__name__
    else:
        msg_type = type(message).__name__

    lines = [
        f"================================ {msg_type} ================================"
    ]

    if hasattr(message, "content"):
        lines.append(f"\n{message.content}\n")
    elif hasattr(message, "model_dump"):
        lines.append(
            f"\n{json.dumps(message.model_dump(), indent=2, ensure_ascii=False)}\n"
        )
    else:
        lines.append(f"\n{str(message)}\n")

    return "\n".join(lines)


async def generate_langgraph_stream(
    graph,
    input_data: Dict[str, Any],
    config: Dict[str, Any],
    stream_mode: str,
    assistant_id: str = "agent",
) -> AsyncGenerator[str]:
    """Generate SSE stream in LangGraph Server API format.

    This uses LangGraph's native streaming with parallel node execution.
    Multiple DeepAgent nodes can run in parallel and their outputs are
    streamed as they arrive.

    Args:
        graph: LangGraph compiled graph (with parallel nodes)
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
        logger.debug(
            f"Input: {json.dumps(input_data, ensure_ascii=False, default=str)[:200]}..."
        )
        logger.debug(f"Config: {json.dumps(config, ensure_ascii=False, default=str)}")

        # Ensure thread_id is in config for checkpointer
        if "configurable" not in config:
            config["configurable"] = {}
        config["configurable"]["thread_id"] = thread_id

        # Send metadata event
        metadata = {"run_id": run_id, "thread_id": thread_id, "attempt": 1}
        yield f"event: metadata\ndata: {json.dumps(metadata, ensure_ascii=False)}\nid: {int(datetime.now().timestamp() * 1000)}-{event_counter}\n\n"
        event_counter += 1

        # Track which nodes we've seen
        seen_nodes = set()

        # Stream the LangGraph agent response using native streaming
        # subgraphs=True enables streaming from DeepAgents inside nodes
        log_step(
            logger,
            "Streaming graph output",
            f"stream_mode={stream_mode}, subgraphs=True",
        )

        # Run parallel stream for logging (updates mode shows complete messages)
        import asyncio

        async def log_updates():
            """Background task to log complete node outputs using updates stream."""
            try:
                async for update in graph.astream(
                    input_data, config=config, stream_mode="updates", subgraphs=True
                ):
                    _, data = update
                    # updates returns {node_name: state_update}
                    for node_key, node_data in data.items():
                        if isinstance(node_data, dict) and "messages" in node_data:
                            messages = node_data["messages"]
                            if messages:
                                # Log the last (complete) message from this node
                                last_msg = (
                                    messages[-1]
                                    if isinstance(messages, list)
                                    else messages
                                )
                                logger.info(
                                    f"[{node_key}]\n{format_message_pretty(last_msg)}"
                                )
            except Exception as e:
                log_error(logger, e, "log_updates background task")

        # Start logging in background
        log_task = asyncio.create_task(log_updates())

        async for chunk in graph.astream(
            input_data, config=config, stream_mode=stream_mode, subgraphs=True
        ):
            try:
                # With subgraphs=True, chunk format is (namespace, data)
                # namespace is a tuple like () for parent or ('node_name:id',) for subgraph
                namespace, data = chunk

                # Extract node name from namespace if available
                if namespace and len(namespace) > 0:
                    # namespace[0] is like "metadata_search:abc123"
                    node_name = namespace[0].split(":")[0]
                else:
                    node_name = "root"

                # Data can be either (message, metadata) tuple or a dict
                if isinstance(data, tuple) and len(data) == 2:
                    message, metadata_chunk = data
                    # Override with namespace node name if different
                    if node_name != "root":
                        metadata_chunk["langgraph_node"] = node_name
                else:
                    # Skip non-message chunks
                    continue

                # Send mode marker when we see a new node
                if node_name not in seen_nodes and node_name != "unknown":
                    seen_nodes.add(node_name)
                    yield f"event: mode\ndata: {json.dumps({'mode': node_name}, ensure_ascii=False)}\nid: {int(datetime.now().timestamp() * 1000)}-{event_counter}\n\n"
                    event_counter += 1

                # Send messages/metadata event (first chunk per node)
                if node_name not in seen_nodes or len(seen_nodes) == 1:
                    messages_metadata = {
                        f"lc_run--{run_id}": {
                            "metadata": {
                                "run_id": run_id,
                                "thread_id": thread_id,
                                "assistant_id": assistant_id,
                                "langgraph_node": node_name,
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
                chunk_json = json.dumps(
                    [message_data], ensure_ascii=False, default=repr
                )
                yield f"event: messages/partial\ndata: {chunk_json}\nid: {int(datetime.now().timestamp() * 1000)}-{event_counter}\n\n"
                event_counter += 1

            except Exception as e:
                # If serialization fails, send error but continue
                log_error(logger, e, "chunk processing")
                error_msg = json.dumps(
                    {"event": "error", "error": str(e)}, ensure_ascii=False
                )
                yield f"event: error\ndata: {error_msg}\nid: {int(datetime.now().timestamp() * 1000)}-{event_counter}\n\n"
                event_counter += 1

        # Wait for logging task to complete
        try:
            await log_task
        except Exception as e:
            log_error(logger, e, "waiting for log_task")

        log_step(
            logger,
            "Stream completed",
            f"total_events={event_counter}, nodes={len(seen_nodes)}",
        )

    except Exception as e:
        log_error(logger, e, "generate_langgraph_stream")
        error_msg = json.dumps({"error": str(e)}, ensure_ascii=False)
        yield f"event: error\ndata: {error_msg}\n\n"
