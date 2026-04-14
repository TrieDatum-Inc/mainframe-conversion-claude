"""
Master API router — aggregates all sub-routers under /api/v1.
"""

from fastapi import APIRouter
from app.api.endpoints import auth, accounts

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(accounts.router)
