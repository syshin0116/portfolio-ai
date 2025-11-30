"""Metadata-only search tool (fast, lightweight)."""

from langchain_core.tools import tool
from src.tools.blog.utils import build_blog_index


# Build blog index once at module load time
BLOG_INDEX = build_blog_index("data/blog")


@tool
def search_blog_metadata(query: str, max_results: int = 10) -> str:
    """Search blog posts using metadata only (title, tags, summary).

    Fast, lightweight search that only looks at metadata fields.
    Returns title, URL, date, tags, and summary for up to 10 posts.

    Args:
        query: Search query (keywords to find in blog posts)
        max_results: Maximum number of results to return (default: 10)

    Returns:
        Formatted string with post summaries and URLs
    """
    query_lower = query.lower()
    results = []

    # Score each blog post based on keyword matches
    for post in BLOG_INDEX:
        score = 0

        # Check title (highest weight)
        if query_lower in post.get("title", "").lower():
            score += 5

        # Check summary and description
        if query_lower in post.get("summary", "").lower():
            score += 3
        if query_lower in post.get("description", "").lower():
            score += 3

        # Check tags
        tags = [str(tag).lower() for tag in post.get("tags", [])]
        if any(query_lower in tag for tag in tags):
            score += 2

        # Check categories
        categories = [str(cat).lower() for cat in post.get("categories", [])]
        if any(query_lower in cat for cat in categories):
            score += 2

        if score > 0:
            results.append((score, post))

    # Sort by score (descending) and limit results
    results.sort(reverse=True, key=lambda x: x[0])
    top_results = results[:max_results]

    if not top_results:
        return f"No blog posts found for query: '{query}'"

    # Format results with summaries only (lightweight)
    formatted_results = []
    for i, (score, post) in enumerate(top_results, 1):
        title = post.get("title", "Untitled")
        date = post.get("date", "")
        url = post.get("url", "")
        tags = ", ".join(str(t) for t in post.get("tags", [])[:5])  # Limit tags
        summary = post.get("summary") or post.get("description", "")

        formatted_post = f"""
{i}. **{title}**
   URL: {url}
   Date: {date}
   Tags: {tags}
   Summary: {summary}
"""
        formatted_results.append(formatted_post)

    return "\n".join(formatted_results)


def get_tools():
    """Return list of tools for metadata search mode."""
    return [search_blog_metadata]
