"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import cards, employees
from src.api.dependencies import shutdown, startup
from src.config import settings

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler.

    Manages startup and shutdown events for the application,
    including initialization of services and cleanup of resources.
    """
    # Startup
    logger.info("=" * 60)
    logger.info("Starting Santa API application")
    logger.info("=" * 60)
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"Max regenerations: {settings.max_regenerations}")

    # Initialize services
    await startup()

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("=" * 60)
    logger.info("Shutting down Santa API application")
    logger.info("=" * 60)

    # Cleanup resources
    await shutdown()

    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Santa API",
    version="1.0.0",
    description="AI-generated corporate greeting cards API",
    debug=settings.debug,
    lifespan=lifespan,
)

# Add CORS middleware
# TODO: Configure proper CORS settings for production (restrict origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Length", "Content-Type", "Cache-Control"],
)

# Include API routers
app.include_router(cards.router, prefix="/api/v1", tags=["cards"])
app.include_router(employees.router, prefix="/api/v1", tags=["employees"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Dictionary with status information.
    """
    return {
        "status": "healthy",
        "service": "santa-api",
        "version": "1.0.0",
    }
