"""Configuration for vector_search agent (TODO: implement)."""

from pathlib import Path


def get_agent_tools():
    """Get tools for vector search agent."""
    # TODO: Implement vector search tools
    return []


def get_skill_docs() -> str:
    """Load SKILL.md documentation for vector search tools."""
    skill_path = Path(__file__).parent.parent.parent / "tools" / "blog" / "vector" / "SKILL.md"

    if not skill_path.exists():
        return ""

    return skill_path.read_text(encoding="utf-8")


# Agent configuration
AGENT_CONFIG = {
    "name": "vector_search",
    "description": "Semantic embedding-based blog search (TODO: implement)",
    "tools": get_agent_tools,
    "skills": get_skill_docs,
}
