"""FastAPI application entry point for the CardDemo Transaction Module.

Converted from:
  COTRN00C (CT00) — Transaction list/browse
  COTRN01C (CT01) — Transaction detail view
  COTRN02C (CT02) — Add transaction
  COBIL00C  (CB00) — Bill payment
  CORPT00C  (CR00) — Transaction reports
"""

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.exceptions.handlers import generic_exception_handler
from app.routers import bill_payment, reports, transactions
from app.routers.auth import create_access_token

app = FastAPI(
    title=settings.app_name,
    description=(
        "Modernized CardDemo Transaction Module. "
        "Converted from COBOL CICS programs: COTRN00C, COTRN01C, COTRN02C, "
        "COBIL00C, CORPT00C."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow frontend (Next.js dev server) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
app.add_exception_handler(Exception, generic_exception_handler)

# Register routers
app.include_router(transactions.router)
app.include_router(bill_payment.router)
app.include_router(reports.router)


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Simple health check endpoint."""
    return {"status": "ok", "service": settings.app_name}


# ---------------------------------------------------------------------------
# Auth router — token issuance (dev/test convenience)
# ---------------------------------------------------------------------------
auth_router = APIRouter(prefix="/api/auth", tags=["auth"])


@auth_router.post("/token", summary="Obtain JWT access token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> dict:
    """Issue a JWT token for development/testing.

    In production this would validate against the USRSEC VSAM file (user table).
    For development, any username/password is accepted to facilitate testing.
    """
    token = create_access_token(user_id=form_data.username, user_type="regular")
    return {"access_token": token, "token_type": "bearer"}


app.include_router(auth_router)
