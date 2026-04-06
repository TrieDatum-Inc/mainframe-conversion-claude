"""FastAPI application entry point for the CardDemo User Administration API."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers.users import router as users_router

app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description=(
        "Admin-only REST API for managing CardDemo users. "
        "Modernised from COBOL programs COUSR00C–COUSR03C."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Basic liveness probe."""
    return {"status": "ok"}
