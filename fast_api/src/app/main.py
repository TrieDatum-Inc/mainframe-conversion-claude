"""FastAPI application entry point for CardDemo API.

Programs converted:
  COSGN00C (CC00) → /auth/login, /auth/logout, /auth/me
  COMEN01C (CM00) → /menu/main, /menu/main/navigate
  COADM01C (CA00) → /menu/admin, /menu/admin/navigate
  CORPT00C (CR00) → /reports
  COBIL00C (CB00) → /payments
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers.auth_router import router as auth_router
from app.routers.menu_router import router as menu_router
from app.routers.payments_router import router as payments_router
from app.routers.reports_router import router as reports_router

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(
    title=f"{settings.app_name} API",
    description=(
        "CardDemo API — converted from IBM COBOL mainframe application.\n\n"
        "**Programs converted:**\n"
        "- `COSGN00C` (Transaction CC00) → `/auth/*` endpoints\n"
        "- `COMEN01C` (Transaction CM00) → `/menu/main*` endpoints\n"
        "- `COADM01C` (Transaction CA00) → `/menu/admin*` endpoints\n"
        "- `CORPT00C` (Transaction CR00) → `/reports` endpoints\n"
        "- `COBIL00C` (Transaction CB00) → `/payments` endpoints\n\n"
        "**Authentication:** JWT bearer token (replaces CICS COMMAREA session state)"
    ),
    version="1.0.0",
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

app.include_router(auth_router)
app.include_router(menu_router)
app.include_router(reports_router)
app.include_router(payments_router)


@app.get("/health", tags=["Health"])
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "app": settings.app_name}
