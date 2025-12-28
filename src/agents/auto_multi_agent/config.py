"""Configuration for auto_multi_agent (supervisor that routes to specialized agents)."""


def get_available_agents() -> list[dict]:
    """Get list of available specialized agents with descriptions.

    Returns list of agent info for routing decisions.
    """
    return [
        {
            "name": "metadata_search",
            "description": "Fast metadata-only search (title, tags, summary). Use for quick lookups.",
        },
        {
            "name": "filesystem_search",
            "description": "Two-step search with summaries and full content access. Use when detailed content analysis needed.",
        },
        # TODO: Uncomment when implemented
        # {
        #     "name": "vector_search",
        #     "description": "Semantic embedding-based search. Use for conceptual similarity.",
        # },
        # {
        #     "name": "graph_search",
        #     "description": "Graph-based exploration of post relationships. Use for discovering connections.",
        # },
    ]


# Agent configuration
AGENT_CONFIG = {
    "name": "auto_multi_agent",
    "description": "Supervisor agent that routes queries to specialized search agents",
    "available_agents": get_available_agents,
}
