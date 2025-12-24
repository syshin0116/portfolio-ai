"""Backend configurations for DeepAgents.

Provides different backend strategies for filesystem access:
- FilesystemBackend: Direct access to blog directory
- CompositeBackend: Hybrid storage (blog + workspace)
"""

from pathlib import Path

from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend


# Blog directory path (project root / data / blog)
BLOG_DIR = Path(__file__).parent.parent.parent / "data" / "blog"


def create_blog_filesystem_backend():
    """Create a simple FilesystemBackend for blog directory access.

    This backend allows the agent to read files from the blog directory
    using filesystem tools (ls, read_file, glob, grep).

    Returns:
        FilesystemBackend configured for blog directory
    """
    return FilesystemBackend(root_dir=str(BLOG_DIR))


def create_blog_composite_backend():
    """Create a CompositeBackend with blog access + temporary workspace.

    This backend provides:
    - /blog/: Read-only access to blog content (FilesystemBackend)
    - /workspace/: Temporary storage for agent work (StateBackend)

    Returns:
        CompositeBackend with hybrid storage

    Example usage by agent:
        read_file("/blog/content/AI/post.md")  # Read blog content
        write_file("/workspace/summary.md", content)  # Temporary notes
    """
    return CompositeBackend(
        default=StateBackend(),  # Default: ephemeral workspace
        routes={
            "/blog/": FilesystemBackend(root_dir=str(BLOG_DIR)),  # Blog directory
        },
    )


# Export default backend
create_default_backend = create_blog_filesystem_backend
