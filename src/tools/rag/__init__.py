"""RAG tools - dynamically loaded based on rag_modes."""

from importlib import import_module
from pathlib import Path
from typing import List


def load_rag_tools(rag_modes: List[str]) -> list:
    """Load tools dynamically based on rag_modes.

    Args:
        rag_modes: List of RAG mode names (e.g., ["metadata_search", "filesystem_search"])

    Returns:
        List of LangChain tool objects
    """
    import logging

    logger = logging.getLogger(__name__)
    tools = []
    rag_tools_dir = Path(__file__).parent

    for mode in rag_modes:
        tool_file = rag_tools_dir / f"{mode}.py"

        if tool_file.exists():
            try:
                # Dynamically import the module
                module = import_module(f"src.tools.rag.{mode}")

                # Get tools from the module
                if hasattr(module, "get_tools"):
                    tools.extend(module.get_tools())
            except Exception as e:
                logger.warning(f"Failed to load tools from {mode}: {e}")
                continue

    return tools


__all__ = ["load_rag_tools"]
