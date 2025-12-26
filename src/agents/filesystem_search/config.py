"""Configuration for filesystem_search agent."""

from pathlib import Path

from src.tools.blog.filesystem.tools import get_tools


def get_agent_tools():
    """Get tools for filesystem search agent."""
    return get_tools()


def get_skill_docs() -> str:
    """Load SKILL.md documentation for filesystem search tools."""
    skill_path = Path(__file__).parent.parent.parent / "tools" / "blog" / "filesystem" / "SKILL.md"

    if not skill_path.exists():
        return ""

    return skill_path.read_text(encoding="utf-8")


# Agent configuration
AGENT_CONFIG = {
    "name": "filesystem_search",
    "description": "Two-step blog search with summaries and full content access",
    "tools": get_agent_tools,
    "skills": get_skill_docs,
    "backend": "filesystem",  # Signals that this agent needs FilesystemBackend
}
