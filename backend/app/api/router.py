"""
Master API router — aggregates all sub-routers under /api/v1.

COBOL origin: Replaces the CICS transaction routing table where each
transaction ID (COSG, CA00, CM00, etc.) maps to a COBOL program.
Here, each router module handles a logical group of endpoints.

As new modules are converted, their routers are registered here.
"""

from fastapi import APIRouter

from app.api.endpoints import auth

# Master router with /api/v1 prefix (set in main.py via app.include_router)
api_router = APIRouter()

# Authentication module — COSGN00C (Transaction: CC00)
api_router.include_router(auth.router)

# Future module routers will be added here as conversion progresses:
# from app.api.endpoints import users, accounts, cards, transactions
# api_router.include_router(users.router)
# api_router.include_router(accounts.router)
# api_router.include_router(cards.router)
# api_router.include_router(transactions.router)
