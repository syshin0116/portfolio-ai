# Multi-stage Dockerfile optimized for uv + Docker
# Based on: https://docs.astral.sh/uv/guides/integration/docker/

# Build stage
FROM python:3.13-slim AS builder

# Install uv from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Set environment variables for build
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY src/ ./src/
COPY static/ ./static/
COPY main.py ./

# Always clone fresh blog content for latest updates (content directory only)
RUN echo "Cloning blog repository..." && \
    rm -rf data/blog && \
    mkdir -p data/blog && \
    cd data/blog && \
    git init && \
    git remote add origin https://github.com/syshin0116/syshin0116.github.io.git && \
    git config core.sparseCheckout true && \
    echo "content/*" >> .git/info/sparse-checkout && \
    git pull --depth 1 origin main

# Install project
RUN uv sync --frozen --no-dev

# Runtime stage
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Copy virtual environment from builder
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy application code from builder
COPY --from=builder --chown=appuser:appuser /app/src /app/src
COPY --from=builder --chown=appuser:appuser /app/data /app/data
COPY --from=builder --chown=appuser:appuser /app/static /app/static
COPY --from=builder --chown=appuser:appuser /app/main.py /app/main.py

# Switch to non-root user
USER appuser

# Expose port (Cloud Run uses PORT env variable)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/health')"

# Run FastAPI server with uvicorn
# Cloud Run injects PORT env variable
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
