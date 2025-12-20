"""System endpoints (health, info, root)."""

from fastapi import APIRouter


router = APIRouter()


@router.get("/")
async def root():
    """Root endpoint."""
    return {"service": "Portfolio AI", "status": "running", "version": "0.0.1"}


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@router.get("/info")
async def info():
    """Get agent information."""
    return {
        "agent": "Portfolio AI",
        "capabilities": [
            "Search blog posts",
            "Get blog content",
            "Answer questions about portfolio",
        ],
        "tools": ["search_blog_summaries", "get_blog_content"],
    }
