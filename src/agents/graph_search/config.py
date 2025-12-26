"""Configuration for graph_search agent (TODO: implement)."""

from pathlib import Path


def get_agent_tools():
    """Get tools for graph search agent."""
    # TODO: Implement graph search tools
    return []


def get_skill_docs() -> str:
    """Load SKILL.md documentation for graph search tools."""
    skill_path = Path(__file__).parent.parent.parent / "tools" / "blog" / "graph" / "SKILL.md"

    if not skill_path.exists():
        return ""

    return skill_path.read_text(encoding="utf-8")


# Agent configuration
AGENT_CONFIG = {
    "name": "graph_search",
    "description": "Graph-based blog exploration (TODO: implement)",
    "tools": get_agent_tools,
    "skills": get_skill_docs,
}
