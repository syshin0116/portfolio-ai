---
name: blog_filesystem_search
description: Two-step blog search with summaries first, then full content access
version: 1.0.0
tools:
  - search_blog_summaries
  - get_blog_content
---

# Blog Filesystem Search

This skill provides a two-step approach to blog search: first get summaries of relevant posts, then fetch full content for selected posts. Optimized for efficient context usage.

## Available Tools

### `search_blog_summaries(query: str, max_results: int = 10)`

**Step 1: Discovery** - Search blog posts and return summaries only.

**When to use:**
- Start every search with this tool
- Get an overview before diving into details
- Find relevant posts efficiently

**What it searches:**
- **Title** (highest priority, weight: 5)
- **Summary/Description** (weight: 3)
- **Tags** (weight: 2)
- **Categories** (weight: 2)

**Returns:**
- Title, URL, date, tags, and summary for up to 10 posts
- Results ranked by relevance score
- Instructions to use `get_blog_content()` for full details

### `get_blog_content(url: str)`

**Step 2: Deep Dive** - Get full markdown content of a specific blog post.

**When to use:**
- After using `search_blog_summaries()` to identify relevant posts
- When you need complete post content
- When summaries don't provide enough information

**Args:**
- `url`: Full blog URL from search results (e.g., `https://syshin0116.github.io/AI/2025-09-07-...`)

**Returns:**
- Complete markdown content including:
  - Title, URL, date, tags
  - Summary
  - Full post content

## Recommended Workflow

### Progressive Disclosure Pattern

1. **Search First** (lightweight):
   ```
   search_blog_summaries("deep learning")
   ```

2. **Review Summaries**:
   - Check titles, tags, and summaries
   - Identify 1-3 most relevant posts

3. **Fetch Details** (only when needed):
   ```
   get_blog_content("https://syshin0116.github.io/AI/2025-09-07-transformer")
   ```

### Why Two Steps?

- **Context Efficiency**: Don't load full content unless needed
- **Better Overview**: See multiple options before diving deep
- **Relevance Filtering**: Summaries help you pick the right posts

## Usage Examples

### Example 1: Find and Read Single Post
```
1. search_blog_summaries("attention mechanism")
2. Review results → Post #2 looks most relevant
3. get_blog_content("https://syshin0116.github.io/.../attention")
```

### Example 2: Compare Multiple Posts
```
1. search_blog_summaries("transformers", max_results=5)
2. get_blog_content(url1)
3. get_blog_content(url2)
4. Compare approaches in both posts
```

### Example 3: Broad Research
```
1. search_blog_summaries("machine learning")
2. Review all 10 summaries
3. Only fetch full content for 2-3 most relevant posts
```

## Important Rules

- **Always start with `search_blog_summaries()`** - Never jump straight to `get_blog_content()`
- **Use exact URLs** from search results - Don't guess or modify URLs
- **Be selective** - Only fetch full content when summaries aren't enough
- **One post at a time** - Call `get_blog_content()` for each post separately

## Limitations

- **Keyword matching**: Uses simple string matching (not semantic search)
- **Static index**: Built at startup, doesn't update dynamically
- **No cross-post search**: Each post searched independently

## When NOT to use

- If metadata search is sufficient → Use `metadata_search` (faster)
- If you need semantic/embedding search → Use `vector_search`
- If you need graph-based exploration → Use `graph_search`

## Tips for Agents

1. **Context Management**:
   - Summaries use ~100 tokens per post
   - Full content can be 1000-5000+ tokens
   - Fetch full content only when necessary

2. **Query Optimization**:
   - Use specific keywords from titles/tags
   - Try multiple related queries if first search fails
   - Adjust `max_results` based on how many options you need

3. **Error Handling**:
   - If URL not found, verify it matches exactly from search results
   - If no results, try broader or different keywords
