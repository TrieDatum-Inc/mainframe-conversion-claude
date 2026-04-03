"""FastAPI application entry point for the Account Management module.

Converted from COBOL CICS programs:
  COACTVWC (Transaction CAVW) → GET /api/accounts/{acct_id}
  COACTUPC (Transaction CAUP) → PUT /api/accounts/{acct_id}
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import accounts_router

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description=(
        "REST API equivalent of the CardDemo Account Management COBOL programs. "
        "COACTVWC (read-only account view) and COACTUPC (account update with "
        "optimistic concurrency control) are served by this API."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(accounts_router)


@app.get("/health", tags=["meta"])
async def health_check() -> dict:
    """Simple health check endpoint."""
    return {"status": "ok", "version": settings.app_version}
