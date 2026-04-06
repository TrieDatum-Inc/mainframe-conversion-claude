"""
Master API router — aggregates all sub-routers under /api/v1.

COBOL origin: Replaces CICS transaction routing table (DFHPCT).
Each sub-router maps to one or more CICS transactions/programs.

Routing table mapping:
  /users             → COUSR00C/01C/02C/03C (CU00/CU01/CU02/CU03) — admin only
  /transaction-types → COTRTLIC (CTLI) + COTRTUPC (CTTU) — admin only
  /accounts          → COACTVWC (view) + COACTUPC (update) — all authenticated users
  /cards             → COCRDLIC (list) + COCRDSLC (view) + COCRDUPC (update) — all users
  /transactions      → COTRN00C (CT00) + COTRN01C (CT01) + COTRN02C (CT02) — all users
  /billing           → COBIL00C (CB00) — all users
  /reports           → CORPT00C (CR00) — all users
"""

from fastapi import APIRouter

from app.api.endpoints import (
    accounts,
    billing,
    credit_cards,
    reports,
    transaction_types,
    transactions,
    users,
)

api_router = APIRouter(prefix="/api/v1")

# User Management — COUSR00C/01C/02C/03C (admin)
api_router.include_router(users.router)

# Transaction Type Management — COTRTLIC (CTLI) + COTRTUPC (CTTU) — admin only
api_router.include_router(transaction_types.router)

# Account Management — COACTVWC (view) + COACTUPC (update) — all authenticated users
api_router.include_router(accounts.router)

# Credit Card Management — COCRDLIC + COCRDSLC + COCRDUPC — all authenticated users
api_router.include_router(credit_cards.router)

# Transaction Management — COTRN00C (CT00) + COTRN01C (CT01) + COTRN02C (CT02) — all users
api_router.include_router(transactions.router)

# Billing — COBIL00C (CB00) — all authenticated users
api_router.include_router(billing.router)

# Reports — CORPT00C (CR00) — all authenticated users
api_router.include_router(reports.router)
