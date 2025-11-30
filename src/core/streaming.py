"""Streaming utilities for LangGraph Server API compatibility."""

import asyncio
import io
import json
import sys
import uuid
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, List

from src.core.logger import get_logger, log_step, log_error

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
    if hasattr(message, '__class__'):
        msg_type = message.__class__.__name__
    else:
        msg_type = type(message).__name__

    lines = [f"================================ {msg_type} ================================"]

    if hasattr(message, "content"):
        lines.append(f"\n{message.content}\n")
    elif hasattr(message, "model_dump"):
        lines.append(f"\n{json.dumps(message.model_dump(), indent=2, ensure_ascii=False)}\n")
    else:
        lines.append(f"\n{str(message)}\n")

    return "\n".join(lines)


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
                logger.debug(format_message_pretty(message))

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


async def generate_multi_agent_stream(
    agents: List,
    rag_modes: List[str],
    input_data: Dict[str, Any],
    config: Dict[str, Any],
    stream_mode: str,
    assistant_id: str = "agent"
) -> AsyncGenerator[str, None]:
    """Generate SSE stream from multiple independent agents running in parallel.

    Each agent processes the same input independently and their results are merged.

    Args:
        agents: List of LangGraph agents (one per RAG mode)
        rag_modes: List of RAG mode names
        input_data: Input data for the graphs
        config: Configuration for graph execution
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

        log_step(logger, "Starting multi-agent stream", f"run_id={run_id}, thread_id={thread_id}, agents={len(agents)}")
        logger.debug(f"RAG modes: {rag_modes}")
        logger.debug(f"Input: {json.dumps(input_data, ensure_ascii=False, default=str)[:200]}...")

        # Ensure thread_id is in config for checkpointer
        if "configurable" not in config:
            config["configurable"] = {}
        config["configurable"]["thread_id"] = thread_id

        # Send metadata event
        metadata = {
            "run_id": run_id,
            "thread_id": thread_id,
            "attempt": 1,
            "rag_modes": rag_modes
        }
        yield f"event: metadata\ndata: {json.dumps(metadata, ensure_ascii=False)}\nid: {int(datetime.now().timestamp() * 1000)}-{event_counter}\n\n"
        event_counter += 1

        # Run all agents in parallel
        async def run_agent(agent, mode_name):
            """Run a single agent and collect its output."""
            result_chunks = []
            async for chunk in agent.astream(input_data, config=config, stream_mode=stream_mode):
                result_chunks.append(chunk)
            return mode_name, result_chunks

        # Execute agents in parallel
        log_step(logger, "Executing agents in parallel", f"count={len(agents)}")
        tasks = [run_agent(agent, mode) for agent, mode in zip(agents, rag_modes)]
        agent_results = await asyncio.gather(*tasks)

        # Stream results from all agents
        for mode_name, chunks in agent_results:
            log_step(logger, f"Streaming results from {mode_name}", f"chunks={len(chunks)}")
            
            # Send mode marker
            yield f"event: mode\ndata: {json.dumps({'mode': mode_name}, ensure_ascii=False)}\nid: {int(datetime.now().timestamp() * 1000)}-{event_counter}\n\n"
            event_counter += 1

            for chunk in chunks:
                try:
                    message, metadata = chunk

                    # Log message content
                    logger.debug(format_message_pretty(message))

                    # Send messages/metadata event (first chunk only per mode)
                    if event_counter == 2:  # After metadata and first mode marker
                        messages_metadata = {
                            f"lc_run--{run_id}": {
                                "metadata": {
                                    "run_id": run_id,
                                    "thread_id": thread_id,
                                    "assistant_id": assistant_id,
                                    "langgraph_node": "model",
                                    "rag_mode": mode_name
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
                    log_error(logger, e, f"chunk processing for {mode_name}")
                    error_msg = json.dumps({"event": "error", "error": str(e), "mode": mode_name}, ensure_ascii=False)
                    yield f"event: error\ndata: {error_msg}\nid: {int(datetime.now().timestamp() * 1000)}-{event_counter}\n\n"
                    event_counter += 1

        log_step(logger, "Multi-agent stream completed", f"total_events={event_counter}")

    except Exception as e:
        log_error(logger, e, "generate_multi_agent_stream")
        error_msg = json.dumps({"error": str(e)}, ensure_ascii=False)
        yield f"event: error\ndata: {error_msg}\n\n"
