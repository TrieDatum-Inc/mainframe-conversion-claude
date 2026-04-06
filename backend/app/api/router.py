"""
Master API router — aggregates all sub-routers under /api/v1.

COBOL origin: Replaces CICS PCT (Program Control Table) transaction routing.
Each router module handles one logical group of COBOL programs.
"""

from fastapi import APIRouter

from app.api.endpoints import accounts, auth, credit_cards, users

api_router = APIRouter()

# Authentication — COSGN00C (Transaction: CC00)
api_router.include_router(auth.router)

# User Management — COUSR00C/01C/02C/03C (admin-only)
api_router.include_router(users.router)

# Account Management — COACTVWC (view) + COACTUPC (update)
api_router.include_router(accounts.router)

# Credit Card Management — COCRDLIC + COCRDSLC + COCRDUPC
api_router.include_router(credit_cards.router)
