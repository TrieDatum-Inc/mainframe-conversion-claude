"""
FastAPI application entry point.

Replaces the CICS region startup and transaction routing.
All CICS transactions are now HTTP endpoints under /api/v1/.

Application lifecycle:
  startup  → database connection pool initialization (replaces CICS region start)
  shutdown → connection pool cleanup (replaces CICS region shutdown)
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import get_settings
from app.database import engine
from app.utils.error_handlers import register_exception_handlers

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — startup and shutdown hooks."""
    # Startup: verify database connectivity
    async with engine.begin() as conn:
        await conn.run_sync(lambda _: None)  # ping
    yield
    # Shutdown: dispose connection pool
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "CardDemo credit card management API — modernized from COBOL/CICS mainframe. "
        "45 COBOL programs converted to FastAPI endpoints with PostgreSQL."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.environment == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handlers (CICS RESP code → HTTP status mapping)
register_exception_handlers(app)

# API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "version": settings.app_version}
