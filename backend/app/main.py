"""
FastAPI application factory.

COBOL origin: Replaces CICS PLT (Program List Table) initialization and
the CICS region startup sequence. The lifespan context manager handles
startup/shutdown events similar to CICS PLTPI/PLTSD programs.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings
from app.database import init_db
from app.exceptions.handlers import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifecycle management.

    COBOL origin: Replaces CICS PLTPI (Program List Table Post-Initialization)
    programs that ran at CICS region startup to initialize resources.

    Startup: validate database connection (replaces CICS VSAM file open)
    Shutdown: clean up connections (replaces CICS VSAM file close)
    """
    # Startup
    await init_db()
    yield
    # Shutdown — SQLAlchemy engine disposes connections automatically


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns a fully configured FastAPI instance with:
    - CORS middleware (replaces CICS cross-region communication controls)
    - API router at /api/v1
    - Global exception handlers
    - OpenAPI documentation at /docs
    """
    app = FastAPI(
        title="CardDemo API",
        description=(
            "Modernized CardDemo mainframe application. "
            "Replaces CICS/COBOL/BMS with FastAPI/PostgreSQL/Next.js."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS — allows the Next.js frontend to call this API
    # In production, cors_origins must list only the exact frontend URL
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Total-Count"],
    )

    # Register all API routes under /api/v1
    app.include_router(api_router, prefix="/api/v1")

    # Register global exception handlers
    register_exception_handlers(app)

    return app


# Module-level app instance — used by uvicorn and tests
app = create_app()
