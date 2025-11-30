"""LangGraph agents with parallel DeepAgent nodes for each RAG mode."""

from __future__ import annotations

import os
from typing import Dict, List, Annotated

from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from src.agent.prompts import DEFAULT_SYSTEM_PROMPT
from src.tools.rag import load_rag_tools


class MultiRagState(TypedDict):
    """State for multi-RAG orchestration."""
    messages: Annotated[list, add_messages]


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


# Cache for DeepAgent instances per RAG mode
_deep_agents: Dict[str, any] = {}


def get_deep_agent(rag_mode: str):
    """Get or create a DeepAgent for a specific RAG mode.

    Each RAG mode has its own independent DeepAgent with dedicated tools.
    DeepAgents internally use the default AgentState.

    Args:
        rag_mode: RAG mode name (e.g., "metadata_search", "filesystem_search")

    Returns:
        Compiled LangGraph DeepAgent
    """
    if rag_mode not in _deep_agents:
        # Load tools specific to this RAG mode
        tools = load_rag_tools([rag_mode])

        # Create isolated DeepAgent (uses default AgentState internally)
        _deep_agents[rag_mode] = create_deep_agent(
            model=model,
            system_prompt=DEFAULT_SYSTEM_PROMPT,
            tools=tools,
            # checkpointer=checkpointer,  # Disabled for now
        )

    return _deep_agents[rag_mode]


def create_rag_node(rag_mode: str):
    """Create a node function for a specific RAG mode.

    This wraps a DeepAgent in a node function that can be added to the StateGraph.

    Args:
        rag_mode: RAG mode name

    Returns:
        Async node function
    """
    async def node_fn(state: MultiRagState, config):
        """Execute the DeepAgent for this RAG mode."""
        deep_agent = get_deep_agent(rag_mode)

        # DeepAgent uses AgentState internally, we just pass messages
        result = await deep_agent.ainvoke(
            {"messages": state["messages"]},
            config=config
        )

        # Return messages from the DeepAgent
        return {"messages": result["messages"]}

    # Set a descriptive name for debugging
    node_fn.__name__ = f"rag_node_{rag_mode}"
    return node_fn


def create_multi_rag_graph(rag_modes: List[str]):
    """Create a StateGraph with parallel DeepAgent nodes for selected RAG modes.

    Each RAG mode runs as an independent DeepAgent node in parallel.
    Results are automatically merged by LangGraph's state management.

    Architecture:
        START → [rag_node_1, rag_node_2, ...] → END
                     (parallel DeepAgents)

    Args:
        rag_modes: List of RAG mode names to activate (from config)

    Returns:
        Compiled StateGraph
    """
    # Create state graph with simple orchestration state
    graph_builder = StateGraph(MultiRagState)

    # Add a node for each RAG mode
    for rag_mode in rag_modes:
        node_fn = create_rag_node(rag_mode)
        graph_builder.add_node(rag_mode, node_fn)

    # Connect START to all RAG mode nodes (parallel execution)
    for rag_mode in rag_modes:
        graph_builder.add_edge(START, rag_mode)

    # Connect all RAG mode nodes to END
    for rag_mode in rag_modes:
        graph_builder.add_edge(rag_mode, END)

    # Compile and return
    # Note: checkpointer disabled for multi-rag graphs to avoid state conflicts
    return graph_builder.compile()


# For backward compatibility - single agent with metadata_search
def get_agent(rag_mode: str = "metadata_search"):
    """Get a single-mode agent (backward compatibility).

    Args:
        rag_mode: RAG mode name

    Returns:
        Compiled graph with single RAG mode
    """
    return create_multi_rag_graph([rag_mode])


# Default graph for backward compatibility
graph = get_agent("metadata_search")
