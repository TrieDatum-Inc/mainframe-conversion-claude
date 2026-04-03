"""FastAPI application entry point for CardDemo Batch Processing Module.

Converted from COBOL batch programs:
- CBTRN02C (Daily Transaction Posting)
- CBTRN03C (Transaction Report Generator)
- CBACT04C (Interest and Fee Calculator)
- CBEXPORT (Data Export)
- CBIMPORT (Data Import)
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers.batch import router as batch_router

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description=(
        "CardDemo Batch Processing Module — modernized from IBM COBOL/VSAM. "
        "Implements CBTRN02C (transaction posting), CBTRN03C (reports), "
        "CBACT04C (interest calculation), CBEXPORT, and CBIMPORT as REST APIs."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(batch_router)


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.app_version}
