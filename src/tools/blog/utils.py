"""Blog content management utilities."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


def extract_frontmatter(file_path: str | Path) -> dict[str, Any]:
    """Extract YAML frontmatter from markdown file.

    Args:
        file_path: Path to markdown file

    Returns:
        Dictionary containing frontmatter fields
    """
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Match YAML frontmatter between --- delimiters
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)

    if not match:
        return {}

    try:
        frontmatter = yaml.safe_load(match.group(1))
        return frontmatter if isinstance(frontmatter, dict) else {}
    except yaml.YAMLError:
        return {}


def get_blog_url(file_path: str | Path) -> str:
    """Generate blog URL from file path.

    Args:
        file_path: Path to markdown file

    Returns:
        Full blog URL (e.g., https://syshin0116.github.io/AI/2025-10-26-title)
    """
    path = Path(file_path)

    # Get path relative to content directory
    # e.g., data/blog/content/AI/2025-10-26-title.md → AI/2025-10-26-title
    parts = path.parts
    try:
        content_idx = parts.index("content")
        relative_parts = parts[content_idx + 1 :]  # Everything after 'content'
    except ValueError:
        return ""

    # Remove .md extension and join with /
    url_path = "/".join(relative_parts)
    if url_path.endswith(".md"):
        url_path = url_path[:-3]

    return f"https://syshin0116.github.io/{url_path}"


def extract_first_image(content: str) -> str:
    """Extract first image URL from markdown content.

    Args:
        content: Markdown content

    Returns:
        First image URL found, or empty string if none
    """
    # Match markdown image syntax: ![alt](url)
    match = re.search(r"!\[.*?\]\((.*?)\)", content)
    if match:
        return match.group(1)

    # Match HTML img tag: <img src="url">
    match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content)
    if match:
        return match.group(1)

    return ""


def get_blog_metadata(file_path: str | Path) -> dict[str, Any]:
    """Get comprehensive metadata from blog post.

    Args:
        file_path: Path to markdown file

    Returns:
        Dictionary with title, summary, description, tags, date, file path, URL, and image
    """
    frontmatter = extract_frontmatter(file_path)

    tags = frontmatter.get("tags") or []
    categories = frontmatter.get("categories") or []

    # Extract first image from content
    content = read_full_content(file_path)
    image = extract_first_image(content)

    return {
        "title": frontmatter.get("title", ""),
        "summary": frontmatter.get("summary", ""),
        "description": frontmatter.get("description", ""),
        "tags": tags if isinstance(tags, list) else [],
        "date": frontmatter.get("date", ""),
        "categories": categories if isinstance(categories, list) else [],
        "image": image,
        "file_path": str(file_path),
        "url": get_blog_url(file_path),
    }


def read_full_content(file_path: str | Path) -> str:
    """Read full markdown content without frontmatter.

    Args:
        file_path: Path to markdown file

    Returns:
        Markdown content without frontmatter
    """
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Remove frontmatter
    content = re.sub(r"^---\s*\n.*?\n---\s*\n", "", content, flags=re.DOTALL)

    return content.strip()


def build_blog_index(content_dir: str | Path) -> list[dict[str, Any]]:
    """Build index of all blog posts with metadata.

    Args:
        content_dir: Path to blog content directory

    Returns:
        List of blog post metadata dictionaries
    """
    content_path = Path(content_dir)
    blog_index = []

    # Find all markdown files recursively
    for md_file in content_path.rglob("*.md"):
        try:
            metadata = get_blog_metadata(md_file)
            # Only include posts with title or summary
            if metadata["title"] or metadata["summary"]:
                blog_index.append(metadata)
        except Exception as e:
            print(f"Warning: Failed to parse {md_file}: {e}")
            continue

    return blog_index
