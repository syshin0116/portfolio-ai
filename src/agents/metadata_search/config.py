"""Configuration for metadata_search agent."""

from pathlib import Path

from src.tools.blog.metadata.tools import get_tools


def get_agent_tools():
    """Get tools for metadata search agent."""
    return get_tools()


def get_skill_docs() -> str:
    """Load SKILL.md documentation for metadata search tools."""
    skill_path = Path(__file__).parent.parent.parent / "tools" / "blog" / "metadata" / "SKILL.md"

    if not skill_path.exists():
        return ""

    return skill_path.read_text(encoding="utf-8")


# Agent configuration
AGENT_CONFIG = {
    "name": "metadata_search",
    "description": "Fast metadata-only blog search agent",
    "tools": get_agent_tools,
    "skills": get_skill_docs,
}
