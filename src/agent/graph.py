"""LangGraph agents with isolated RAG modes."""

from __future__ import annotations

import os
from typing import Dict

from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from typing_extensions import TypedDict

from src.agent.prompts import DEFAULT_SYSTEM_PROMPT
from src.tools.rag import load_rag_tools


class Context(TypedDict):
    """Context parameters for the agent.

    Set these when creating assistants OR when invoking the graph.
    See: https://langchain-ai.github.io/langgraph/cloud/how-tos/configuration_cloud/
    """

    model_name: str = "gpt-4.1-nano"


model = init_chat_model(
    Context.model_name, model_provider="openai", api_key=os.getenv("OPENAI_API_KEY")
)

# Setup Supabase/Postgres checkpointer for conversation memory (async)
checkpointer = None
if os.getenv("SUPABASE_CONNECTION_STRING"):
    checkpointer = AsyncPostgresSaver.from_conn_string(
        os.getenv("SUPABASE_CONNECTION_STRING")
    )
    # Note: AsyncPostgresSaver.setup() will be called automatically on first use


# Create independent DeepAgent for each RAG mode
_agents: Dict[str, any] = {}


def get_agent(rag_mode: str):
    """Get or create an isolated DeepAgent for a specific RAG mode.

    Each RAG mode has its own independent agent with dedicated tools.
    This ensures complete isolation between different search strategies.

    Args:
        rag_mode: RAG mode name (e.g., "metadata_search", "filesystem_search")

    Returns:
        Compiled LangGraph DeepAgent
    """
    if rag_mode not in _agents:
        # Load tools specific to this RAG mode
        tools = load_rag_tools([rag_mode])

        # Create isolated agent
        _agents[rag_mode] = create_deep_agent(
            model=model,
            system_prompt=DEFAULT_SYSTEM_PROMPT,
            tools=tools,
            # checkpointer=checkpointer,
        )

    return _agents[rag_mode]


# Default graph for backward compatibility (metadata_search)
graph = get_agent("metadata_search")
