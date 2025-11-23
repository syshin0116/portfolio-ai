"""Test blog search functionality."""

# Direct imports to avoid loading graph.py (which requires API keys)
from src.agent.blog_utils import build_blog_index, read_full_content

BLOG_INDEX = build_blog_index("data/blog/content")

# Simplified search function for testing
def test_search_blog(query: str, max_results: int = 3) -> str:
    query_lower = query.lower()
    results = []

    for post in BLOG_INDEX:
        score = 0
        if query_lower in post.get("title", "").lower():
            score += 5
        if query_lower in post.get("summary", "").lower():
            score += 3
        if query_lower in post.get("description", "").lower():
            score += 3

        tags = [str(tag).lower() for tag in post.get("tags", [])]
        if any(query_lower in tag for tag in tags):
            score += 2

        if score > 0:
            results.append((score, post))

    results.sort(reverse=True, key=lambda x: x[0])
    top_results = results[:max_results]

    if not top_results:
        return f"No blog posts found for query: '{query}'"

    formatted_results = []
    for score, post in top_results:
        title = post.get("title", "Untitled")
        date = post.get("date", "")
        tags = ", ".join(str(t) for t in post.get("tags", []))[:50]
        summary = (post.get("summary", "") or post.get("description", ""))[:100]

        formatted_post = f"[Score: {score}] {title} ({date})\nTags: {tags}\nSummary: {summary}..."
        formatted_results.append(formatted_post)

    return "\n\n".join(formatted_results)

# Test 1: Check blog index
print(f"Total blog posts indexed: {len(BLOG_INDEX)}")
print("\nFirst 3 posts:")
for post in BLOG_INDEX[:3]:
    print(f"  - {post['title']} ({post.get('date', 'no date')})")

# Test 2: Search for specific topics
test_queries = [
    "캐싱",
    "Docker",
    "RAG",
]

for query in test_queries:
    print(f"\n{'='*60}")
    print(f"Search query: '{query}'")
    print(f"{'='*60}")
    result = test_search_blog(query, max_results=2)
    print(result)
