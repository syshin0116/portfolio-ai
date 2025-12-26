---
name: blog_metadata_search
description: Fast metadata-only blog search using title, tags, and summaries
version: 1.0.0
tools:
  - search_blog_metadata
---

# Blog Metadata Search

This skill provides fast, lightweight search capabilities for blog posts using metadata only (title, tags, summary). Perfect for quick lookups when you don't need full content.

## Available Tools

### `search_blog_metadata(query: str, max_results: int = 10)`

Searches blog posts using metadata fields only. This is the fastest search method but doesn't access full content.

**When to use:**
- Quick lookups by title, tag, or topic
- Finding posts without reading full content
- Getting overview of available posts on a topic
- Memory-efficient searches

**What it searches:**
- **Title** (highest priority, weight: 5)
- **Summary/Description** (weight: 3)
- **Tags** (weight: 2)
- **Categories** (weight: 2)

**Returns:**
- Title, URL, date, tags, and summary for up to 10 posts
- Results ranked by relevance score

## Usage Pattern

1. **Simple search:**
   ```
   search_blog_metadata("machine learning")
   ```

2. **Limit results:**
   ```
   search_blog_metadata("python", max_results=5)
   ```

## Limitations

- **No full content access**: Only searches metadata fields
- **Keyword matching**: Uses simple string matching (not semantic search)
- **Summary only**: Returns summaries, not full post content
- **Static index**: Built at startup, doesn't update dynamically

## When NOT to use

- If you need to search within blog post content → Use filesystem_search tools
- If you need semantic/embedding search → Use vector_search tools
- If you need graph-based exploration → Use graph_search tools

## Tips

- Use specific keywords from titles or tags for better results
- Check the returned URLs - you can use them with other tools to get full content
- Start broad, then narrow down with more specific queries
