"""New LangGraph Agent.

This module defines a custom graph.
"""

# Lazy import to avoid loading graph.py (and requiring API keys) on module import
# graph is imported only when explicitly accessed
__all__ = ["graph"]


def __getattr__(name):
    if name == "graph":
        from src.agent.graph import graph

        return graph
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
