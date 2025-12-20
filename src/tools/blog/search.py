"""Blog search functionality with 2-stage retrieval."""

from __future__ import annotations

from langchain_core.tools import tool

from src.tools.blog.utils import build_blog_index, read_full_content

# Build blog index once at module load time
BLOG_INDEX = build_blog_index("data/blog")


@tool
def search_blog_summaries(query: str, max_results: int = 10) -> str:
    """Search blog posts and return summaries only (lightweight).

    Use this FIRST to get an overview of relevant posts. Returns title, URL,
    date, tags, and summary for up to 10 posts. Then use get_blog_content
    to fetch full content of specific posts.

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
{i}. Title: {title}
   URL: {url}
   Date: {date}
   Tags: {tags}
   Summary: {summary}
"""
        formatted_results.append(formatted_post)

    header = f"Found {len(top_results)} relevant posts (showing summaries):\n"
    footer = "\nUse get_blog_content(url) to read full content of specific posts."

    return header + "\n".join(formatted_results) + footer


@tool
def get_blog_content(url: str) -> str:
    """Get full content of a specific blog post by URL.

    Use this AFTER search_blog_summaries to get detailed content of selected posts.

    Args:
        url: Full blog URL (e.g., https://syshin0116.github.io/AI/2025-09-07-...)

    Returns:
        Full markdown content of the blog post
    """
    # Find post by URL
    post = None
    for p in BLOG_INDEX:
        if p.get("url") == url:
            post = p
            break

    if not post:
        return f"Blog post not found: {url}"

    # Read full content
    try:
        content = read_full_content(post["file_path"])
    except Exception as e:
        return f"Error reading blog post: {e}"

    title = post.get("title", "Untitled")
    date = post.get("date", "")
    tags = ", ".join(str(t) for t in post.get("tags", []))
    summary = post.get("summary") or post.get("description", "")

    formatted_post = f"""
# {title}

**URL:** {url}
**Date:** {date}
**Tags:** {tags}

## Summary
{summary}

## Full Content
{content}
"""

    return formatted_post
