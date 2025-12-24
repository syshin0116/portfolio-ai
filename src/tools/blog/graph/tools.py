"""Graph search tools (knowledge graph with entity relationships)."""

from langchain_core.tools import tool


@tool
def graph_search_blog(query: str, max_hops: int = 2) -> str:
    """Search blog posts using knowledge graph.

    Explores entity relationships and performs multi-hop reasoning
    across posts. Best for complex queries requiring connections.

    Args:
        query: Search query (complex question requiring relationships)
        max_hops: Maximum relationship hops to explore (default: 2)

    Returns:
        Formatted string with connected posts and relationships
    """
    # TODO: Implement graph search
    # 1. Build/load knowledge graph from blog posts
    # 2. Extract entities and relationships
    # 3. Perform graph traversal based on query
    # 4. Return connected posts with relationship context

    return "Graph search not yet implemented. Please use metadata_search or filesystem_search."


def get_tools():
    """Return list of tools for graph search mode."""
    return [graph_search_blog]
