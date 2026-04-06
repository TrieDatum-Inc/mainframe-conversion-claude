"""
CardDemo Authorization API — FastAPI main application.

Modernizes the COBOL CardDemo Authorization Sub-Application:
- COPAUA0C (MQ authorization engine) → POST /api/authorizations/process
- COPAUS0C (summary view)           → GET  /api/authorizations/{account_id}
- COPAUS1C (detail view)            → GET  /api/authorizations/{account_id}/details/{detail_id}
- COPAUS2C (fraud mark/remove)      → POST /api/authorizations/details/{detail_id}/fraud
- CBPAUP0C (batch purge)            → POST /api/authorizations/purge
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers.authorizations import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    yield


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description=(
        "Authorization processing and fraud management API. "
        "Converted from COBOL CardDemo Authorization Sub-Application "
        "(IMS/DB2/MQ-based)."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": settings.app_version}
