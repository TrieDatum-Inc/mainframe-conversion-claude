"""
FastAPI application factory.

Creates and configures the CardDemo API application:
  - CORS middleware (allows Next.js frontend origin)
  - Security headers middleware
  - Rate limiting (slowapi)
  - Global exception handlers
  - API router mounted at /api/v1

COBOL origin: Replaces the CICS region startup and transaction routing table.
"""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings
from app.exceptions.handlers import register_exception_handlers
from app.middleware.security_headers import SecurityHeadersMiddleware

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown hooks."""
    logger.info(
        "carddemo_api_starting",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
    )
    yield
    logger.info("carddemo_api_stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Refactoring note (security review finding #4):
    # docs_url / redoc_url / openapi_url are now gated on settings.DEBUG.
    # In production (DEBUG=False) all three are set to None, removing the API
    # schema from the publicly accessible surface area.
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "CardDemo Credit Card Management System — modernized from COBOL/CICS/BMS "
            "mainframe application to FastAPI + PostgreSQL."
        ),
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # CORS — allow Next.js frontend to make cross-origin requests
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Total-Count", "X-Page", "X-Page-Size"],
    )

    # Security headers on every response
    app.add_middleware(SecurityHeadersMiddleware)

    # Rate limiting via slowapi.
    # Refactoring note (security review finding #1):
    # The Limiter instance is imported from app.utils.rate_limit so that the
    # same object is registered on app.state here AND referenced by the
    # @limiter.limit() decorator in endpoint modules. Two separate Limiter
    # instances would not share state, silently defeating rate limiting.
    try:
        from slowapi import _rate_limit_exceeded_handler
        from slowapi.errors import RateLimitExceeded
        from app.utils.rate_limit import limiter

        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        logger.info("rate_limiting_enabled")
    except ImportError:
        logger.warning("slowapi_not_installed_rate_limiting_disabled")

    # Global exception handlers
    register_exception_handlers(app)

    # Mount all API routes
    app.include_router(api_router)

    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint for load balancers and monitoring."""
        return {"status": "healthy", "version": settings.APP_VERSION}

    return app


app = create_app()
