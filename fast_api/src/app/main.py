"""FastAPI application entry point for User Administration module.

Converted from CardDemo COBOL programs:
    COUSR00C (CU00) — User List
    COUSR01C (CU01) — User Add
    COUSR02C (CU02) — User Update
    COUSR03C (CU03) — User Delete
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers.users import router as users_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description=(
        "User Administration API converted from CardDemo COBOL programs "
        "COUSR00C/COUSR01C/COUSR02C/COUSR03C. "
        "All endpoints require admin role (X-User-Type: A header)."
    ),
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)


@app.get("/api/health", tags=["health"])
async def health_check() -> dict:
    """Simple health check endpoint."""
    return {"status": "ok", "version": settings.app_version}
