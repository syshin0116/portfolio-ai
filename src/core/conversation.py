"""Conversation history management utilities.

This module provides utilities to:
1. Retrieve conversation history from checkpoints
2. List all conversations for a user
3. Delete conversations
4. Get conversation metadata
"""

from __future__ import annotations

from typing import Any, Dict, List
from uuid import uuid4

from langgraph.checkpoint.base import CheckpointTuple

from src.core.database import get_supabase_client
from src.core.logger import get_logger


logger = get_logger(__name__)


async def get_conversation_history(
    thread_id: str,
    limit: int | None = None,
) -> List[Dict[str, Any]]:
    """Get conversation history for a thread.

    Args:
        thread_id: Thread ID to get history for
        limit: Maximum number of messages to return (newest first)

    Returns:
        List of message dictionaries with role and content

    Example:
        ```python
        messages = await get_conversation_history("thread-123", limit=10)
        for msg in messages:
            print(f"{msg['role']}: {msg['content']}")
        ```
    """
    try:
        client = get_supabase_client()
        checkpointer = client.checkpointer

        # Get checkpoint history for the thread
        config = {"configurable": {"thread_id": thread_id}}
        checkpoints: List[CheckpointTuple] = []

        async for checkpoint_tuple in checkpointer.alist(config):
            checkpoints.append(checkpoint_tuple)
            if limit and len(checkpoints) >= limit:
                break

        # Extract messages from checkpoints
        messages = []
        for checkpoint_tuple in reversed(checkpoints):  # Oldest first
            checkpoint = checkpoint_tuple.checkpoint
            if (
                "channel_values" in checkpoint
                and "messages" in checkpoint["channel_values"]
            ):
                for msg in checkpoint["channel_values"]["messages"]:
                    messages.append(
                        {
                            "role": getattr(msg, "type", "unknown"),
                            "content": getattr(msg, "content", ""),
                            "timestamp": checkpoint.get("ts"),
                        }
                    )

        return messages[-limit:] if limit else messages

    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        return []


async def list_conversations(
    user_id: str | None = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """List all conversations, optionally filtered by user.

    Args:
        user_id: Optional user ID to filter by
        limit: Maximum number of conversations to return

    Returns:
        List of conversation metadata

    Example:
        ```python
        conversations = await list_conversations(user_id="user-123")
        for conv in conversations:
            print(f"Thread: {conv['thread_id']} - {conv['message_count']} messages")
        ```
    """
    try:
        client = get_supabase_client()
        checkpointer = client.checkpointer

        # Get all checkpoints (this is expensive for large datasets)
        # Consider adding a separate table to track thread metadata
        conversations: Dict[str, Dict[str, Any]] = {}

        async for checkpoint_tuple in checkpointer.alist({}):
            config = checkpoint_tuple.config
            thread_id = config.get("configurable", {}).get("thread_id")

            if not thread_id:
                continue

            if thread_id not in conversations:
                conversations[thread_id] = {
                    "thread_id": thread_id,
                    "message_count": 0,
                    "last_updated": None,
                    "first_message": None,
                }

            checkpoint = checkpoint_tuple.checkpoint
            conversations[thread_id]["message_count"] += 1

            # Update last_updated timestamp
            ts = checkpoint.get("ts")
            if ts and (
                not conversations[thread_id]["last_updated"]
                or ts > conversations[thread_id]["last_updated"]
            ):
                conversations[thread_id]["last_updated"] = ts

            # Store first message as preview
            if (
                "channel_values" in checkpoint
                and "messages" in checkpoint["channel_values"]
            ):
                messages = checkpoint["channel_values"]["messages"]
                if messages and not conversations[thread_id]["first_message"]:
                    conversations[thread_id]["first_message"] = getattr(
                        messages[0], "content", ""
                    )[:100]

        # Convert to list and sort by last_updated
        result = list(conversations.values())
        result.sort(key=lambda x: x.get("last_updated") or "", reverse=True)

        return result[:limit]

    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        return []


async def delete_conversation(thread_id: str) -> bool:
    """Delete a conversation and all its checkpoints.

    Args:
        thread_id: Thread ID to delete

    Returns:
        True if successful, False otherwise

    Example:
        ```python
        success = await delete_conversation("thread-123")
        if success:
            print("Conversation deleted")
        ```
    """
    try:
        client = get_supabase_client()

        # Use raw SQL to delete checkpoints for this thread
        # AsyncPostgresSaver doesn't have a delete method yet
        await client.execute_command(
            """
            DELETE FROM checkpoints
            WHERE thread_id = %s
            """,
            (thread_id,),
        )

        await client.execute_command(
            """
            DELETE FROM checkpoint_writes
            WHERE thread_id = %s
            """,
            (thread_id,),
        )

        logger.info(f"Deleted conversation: {thread_id}")
        return True

    except Exception as e:
        logger.error(f"Error deleting conversation {thread_id}: {e}")
        return False


async def get_checkpoint_metadata(thread_id: str) -> Dict[str, Any] | None:
    """Get metadata for a specific checkpoint/thread.

    Args:
        thread_id: Thread ID to get metadata for

    Returns:
        Checkpoint metadata or None if not found

    Example:
        ```python
        metadata = await get_checkpoint_metadata("thread-123")
        if metadata:
            print(f"Last updated: {metadata['last_updated']}")
        ```
    """
    try:
        client = get_supabase_client()
        checkpointer = client.checkpointer

        config = {"configurable": {"thread_id": thread_id}}

        # Get the latest checkpoint
        async for checkpoint_tuple in checkpointer.alist(config, limit=1):
            checkpoint = checkpoint_tuple.checkpoint
            return {
                "thread_id": thread_id,
                "last_updated": checkpoint.get("ts"),
                "checkpoint_ns": checkpoint.get("checkpoint_ns"),
                "metadata": checkpoint_tuple.metadata,
            }

        return None

    except Exception as e:
        logger.error(f"Error getting checkpoint metadata: {e}")
        return None


def generate_thread_id() -> str:
    """Generate a new unique thread ID.

    Returns:
        New thread ID string

    Example:
        ```python
        thread_id = generate_thread_id()
        config = {"configurable": {"thread_id": thread_id}}
        ```
    """
    return f"thread-{uuid4()}"
