"""
Main API router — registers all endpoint modules.
Add new module routers here as they are built.
"""
from fastapi import APIRouter

from app.api.endpoints.authorizations import router as authorizations_router

api_router = APIRouter()

# Authorization module — replaces COPAUS0C, COPAUS1C, COPAUS2C
api_router.include_router(authorizations_router)
