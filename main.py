"""FastAPI production server for Portfolio AI.

This wraps the LangGraph agent for production deployment.
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

# Import routers
from src.api.routes import system_router, chat_router, runs_router

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
app.include_router(chat_router, tags=["Chat"])
app.include_router(runs_router, tags=["Runs"])


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
