"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.api import auth, cards, employees
from src.api.dependencies import get_gemini_client, get_telegram_client, shutdown, startup
from src.config import settings

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

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

# Add rate limiter state and exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Length", "Content-Type", "Cache-Control"],
)

# Include API routers
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(cards.router, prefix="/api/v1", tags=["cards"])
app.include_router(employees.router, prefix="/api/v1", tags=["employees"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Basic health check endpoint.

    Returns:
        Dictionary with status information.
    """
    return {
        "status": "healthy",
        "service": "santa-api",
        "version": "1.0.0",
    }


@app.get("/health/detailed")
async def detailed_health_check() -> dict:
    """Detailed health check including external services.

    Checks connectivity to Gemini API and Telegram Bot API.

    Returns:
        Dictionary with detailed status information for all services.
    """
    services = {}

    # Check Gemini API
    try:
        gemini_client = get_gemini_client()
        # Simple connectivity check - verify client is initialized
        services["gemini"] = {
            "status": "healthy",
            "model": settings.gemini_text_model,
        }
    except Exception as e:
        services["gemini"] = {
            "status": "unhealthy",
            "error": str(e),
        }

    # Check Telegram Bot
    try:
        telegram_client = get_telegram_client()
        # Verify bot can connect
        bot_info = await telegram_client._bot.get_me()
        services["telegram"] = {
            "status": "healthy",
            "bot_username": bot_info.username,
        }
    except Exception as e:
        services["telegram"] = {
            "status": "unhealthy",
            "error": str(e),
        }

    # Determine overall status
    all_healthy = all(s.get("status") == "healthy" for s in services.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "service": "santa-api",
        "version": "1.0.0",
        "services": services,
    }
