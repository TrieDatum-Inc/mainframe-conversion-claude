"""
FastAPI application factory.
Registers middleware, exception handlers, and API routers.
Replaces: CICS application controller / CEDA definitions.
"""
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings
from app.exceptions.handlers import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan — startup and shutdown hooks.
    Replaces: CICS startup tasks and PLT (Program Load Table) initialization.
    """
    # Startup: verify DB connectivity (replaces CICS DB2ENTRY CONNECT)
    yield
    # Shutdown: close engine connections (replaces CICS TERM)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.project_name,
        description=(
            "CardDemo mainframe modernization API. "
            "Replaces COPAUS0C (CPVS), COPAUS1C (CPVD), COPAUS2C authorization programs."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS (replaces CICS cross-region communication)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register exception handlers
    register_exception_handlers(app)

    # Register API routes
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/health")
    async def health_check() -> dict:
        """Health check endpoint."""
        return {"status": "ok", "service": settings.project_name}

    return app


app = create_app()
