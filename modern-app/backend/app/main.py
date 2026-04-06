"""FastAPI application entry point for CardDemo backend."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import accounts, auth, cards, transaction_types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_application() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(
        title=settings.app_title,
        version=settings.app_version,
        description=(
            "CardDemo REST API — modernized from COBOL/CICS mainframe. "
            "Implements COSGN00C authentication, COMEN01C user menu, "
            "and COADM01C admin menu navigation."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(transaction_types.router)
    app.include_router(accounts.router)
    app.include_router(cards.router)

    @app.get("/health", tags=["Health"])
    async def health_check() -> dict:
        """Service health probe."""
        return {"status": "ok", "service": settings.app_title}

    return app


app = create_application()
