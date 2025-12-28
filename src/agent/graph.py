"""LangGraph agents with parallel DeepAgent nodes for each RAG mode."""

from __future__ import annotations

import os
from typing import Annotated, Dict, List

from deepagents import create_deep_agent
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from src.agent.backends import create_default_backend


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

# Setup checkpointer for conversation memory (async)
# TODO: Configure AsyncPostgresSaver once pooler credentials are resolved
# For now, using MemorySaver to get the server running
_checkpointer_conn_string = os.getenv("SUPABASE_CONNECTION_STRING")
checkpointer = None


async def init_checkpointer():
    """Initialize the global checkpointer instance.

    This should be called on application startup.
    """
    global checkpointer
    if checkpointer is None:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

        from src.core.logger import get_logger

        logger = get_logger(__name__)

        if _checkpointer_conn_string:
            logger.info("Initializing AsyncPostgresSaver with Supabase...")
            async with AsyncPostgresSaver.from_conn_string(
                _checkpointer_conn_string
            ) as saver:
                await saver.setup()
                checkpointer = saver
                logger.info("AsyncPostgresSaver initialized successfully")
        else:
            logger.warning(
                "Using MemorySaver - conversation history will not persist across restarts. "
                "Configure SUPABASE_CONNECTION_STRING for persistent storage."
            )
            checkpointer = MemorySaver()


# Cache for agent instances per RAG mode
_agents: Dict[str, any] = {}


def get_agent_for_rag_mode(rag_mode: str):
    """Get or create an agent for a specific RAG mode.

    metadata_search uses a simple agent (fast, no subgraph overhead).
    Other RAG modes use DeepAgent (for complex multi-step reasoning).

    Args:
        rag_mode: RAG mode name (e.g., "metadata_search", "filesystem_search")

    Returns:
        Compiled LangGraph agent (either simple agent or DeepAgent)
    """
    if rag_mode not in _agents:
        # Import agent config dynamically
        try:
            agent_module = __import__(
                f"src.agents.{rag_mode}", fromlist=["AGENT_CONFIG", "SYSTEM_PROMPT"]
            )
            agent_config = agent_module.AGENT_CONFIG
            agent_system_prompt = agent_module.SYSTEM_PROMPT
        except ImportError:
            raise ValueError(f"Unknown RAG mode: {rag_mode}")

        # Get tools from agent config
        tools = agent_config["tools"]()

        # Load SKILL.md documentation
        skill_docs = agent_config["skills"]()

        # Combine system prompt with skill documentation
        full_system_prompt = agent_system_prompt
        if skill_docs:
            full_system_prompt = f"{agent_system_prompt}\n\n# Tool Documentation\n\n{skill_docs}"

        if rag_mode == "metadata_search":
            # Simple agent for metadata search (no deep reasoning needed)
            _agents[rag_mode] = create_agent(
                model=model,
                tools=tools,
            )
        else:
            # DeepAgent for complex RAG modes (vector, graph, filesystem, etc.)
            # Check if agent needs special backend (e.g., FilesystemBackend)
            backend = None
            if agent_config.get("backend") == "filesystem":
                backend = create_default_backend()

            _agents[rag_mode] = create_deep_agent(
                model=model,
                system_prompt=full_system_prompt,
                tools=tools,
                backend=backend,
                # checkpointer=checkpointer,  # Disabled for now
            )

    return _agents[rag_mode]


def create_multi_rag_graph(rag_modes: List[str]):
    """Create a StateGraph with parallel agent nodes for selected RAG modes.

    Each RAG mode runs as an independent agent node in parallel:
    - metadata_search: simple agent (fast, lightweight)
    - others: DeepAgent (complex reasoning with tool calling)

    Results are automatically merged by LangGraph's state management.

    Architecture:
        START → [agent_1, agent_2, ...] → END
                  (parallel agents)

    Args:
        rag_modes: List of RAG mode names to activate (from config)

    Returns:
        Compiled StateGraph
    """
    # Create state graph with simple orchestration state
    graph_builder = StateGraph(MultiRagState)

    # Add agent as a node for each RAG mode
    for rag_mode in rag_modes:
        agent = get_agent_for_rag_mode(rag_mode)
        graph_builder.add_node(rag_mode, agent)

    # Connect START to all RAG mode nodes (parallel execution)
    for rag_mode in rag_modes:
        graph_builder.add_edge(START, rag_mode)

    # Connect all RAG mode nodes to END
    for rag_mode in rag_modes:
        graph_builder.add_edge(rag_mode, END)

    # Compile with checkpointer for conversation memory
    # Each thread_id in config will have its own checkpoint history
    return graph_builder.compile(checkpointer=checkpointer)


def create_auto_single_agent_graph():
    """Create AUTO mode graph with single agent that has all tools.

    The agent automatically selects appropriate tools based on the query.
    Uses SKILL.md documentation to guide tool selection.

    Returns:
        Compiled StateGraph with auto_single_agent
    """
    return create_multi_rag_graph(["auto_single_agent"])


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
