"""FastAPI production server for Portfolio AI.

This wraps the LangGraph agent for production deployment.
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

# Setup logging
from src.core.logger import get_logger, setup_logging

setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger(__name__)

# Import routers
from src.api.routes import runs_router, system_router

logger.info("Starting Portfolio AI application")

app = FastAPI(
    title="Portfolio AI",
    description="AI assistant for Syshin's portfolio",
    version="0.0.1",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(system_router, tags=["System"])
app.include_router(runs_router, tags=["Runs"])


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
