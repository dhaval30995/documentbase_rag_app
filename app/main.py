"""
FastAPI application entry point.
Initializes the app, registers routers, configures CORS, and sets up logging.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import setup_logging
from app.database.postgres import init_db
from app.routers import auth_router, chat_router, document_router, session_router

# Configure logging on module load
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle events."""
    # Startup
    logger.info("Starting RAG Chatbot API...")
    await init_db()
    logger.info("Database tables initialized")
    yield
    # Shutdown
    logger.info("Shutting down RAG Chatbot API...")


# Create FastAPI application
app = FastAPI(
    title="RAG Chatbot API",
    description="A production-grade RAG chatbot that allows users to upload PDFs and chat with them.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router.router)
app.include_router(document_router.router)
app.include_router(chat_router.router)
app.include_router(session_router.router)


@app.get("/", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "RAG Chatbot API"}
