"""Shared models for RAG tools."""

from pydantic import BaseModel, Field


class Source(BaseModel):
    """Source citation for blog posts (compatible with Prompt Kit Source component)."""

    href: str = Field(description="Full URL to the blog post")
    title: str = Field(description="Title of the blog post")
    description: str = Field(description="Summary or description of the post")
