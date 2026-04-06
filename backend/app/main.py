"""
FastAPI application factory for the CardDemo backend.

COBOL origin: Replaces CICS region startup and transaction definitions.
The lifespan hook replaces PLTPI/PLTSD (program list table) processing.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings
from app.database import init_db
from app.exceptions.handlers import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup/shutdown lifecycle."""
    await init_db()
    yield


app = FastAPI(
    title="CardDemo API",
    description="CardDemo mainframe modernization — FastAPI backend",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Next.js frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
register_exception_handlers(app)

# Mount all API routes
app.include_router(api_router)
