"""Configuration for auto_single_agent (one agent with all tools)."""

from pathlib import Path

from src.tools.blog.filesystem.tools import get_tools as get_filesystem_tools
from src.tools.blog.metadata.tools import get_tools as get_metadata_tools


def get_agent_tools():
    """Get ALL tools for single agent auto search."""
    all_tools = []

    # Metadata tools
    all_tools.extend(get_metadata_tools())

    # Filesystem tools
    all_tools.extend(get_filesystem_tools())

    # TODO: Add vector and graph tools when implemented
    # all_tools.extend(get_vector_tools())
    # all_tools.extend(get_graph_tools())

    return all_tools


def get_skill_docs() -> str:
    """Load ALL SKILL.md documentation for single agent."""
    skills_root = Path(__file__).parent.parent.parent / "tools" / "blog"

    all_skills = []

    # Load each tool module's SKILL.md
    for skill_module in ["metadata", "filesystem"]:  # TODO: add "vector", "graph"
        skill_path = skills_root / skill_module / "SKILL.md"
        if skill_path.exists():
            skill_content = skill_path.read_text(encoding="utf-8")
            all_skills.append(f"## {skill_module.upper()} TOOLS\n\n{skill_content}")

    return "\n\n---\n\n".join(all_skills)


# Agent configuration
AGENT_CONFIG = {
    "name": "auto_single_agent",
    "description": "Single agent that selects appropriate tools automatically",
    "tools": get_agent_tools,
    "skills": get_skill_docs,
    "backend": "filesystem",  # Needs filesystem access
}
