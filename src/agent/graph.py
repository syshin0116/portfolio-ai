"""LangGraph single-node graph template.

Returns a predefined response. Replace logic and configuration as needed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from langgraph.graph import StateGraph
from langgraph.runtime import Runtime
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from typing_extensions import TypedDict
from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model
from src.agent.prompts import DEFAULT_SYSTEM_PROMPT
from src.tools.blog import search_blog_summaries, get_blog_content
import os


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

graph = create_deep_agent(
    model=model,
    system_prompt=DEFAULT_SYSTEM_PROMPT,
    tools=[search_blog_summaries, get_blog_content],
    checkpointer=checkpointer,
)
