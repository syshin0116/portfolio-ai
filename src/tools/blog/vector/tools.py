"""Vector search tools (semantic similarity using embeddings)."""

from langchain_core.tools import tool


@tool
def vector_search_blog(query: str, max_results: int = 10) -> str:
    """Search blog posts using semantic similarity (embeddings).

    Finds posts by meaning rather than exact keyword matches.
    Best for conceptual queries.

    Args:
        query: Search query (natural language question or topic)
        max_results: Maximum number of results to return (default: 10)

    Returns:
        Formatted string with posts ranked by semantic similarity
    """
    # TODO: Implement vector search
    # 1. Load/create vector index (ChromaDB, FAISS, etc.)
    # 2. Embed the query
    # 3. Find similar posts
    # 4. Return formatted results

    return "Vector search not yet implemented. Please use metadata_search or filesystem_search."


def get_tools():
    """Return list of tools for vector search mode."""
    return [vector_search_blog]
