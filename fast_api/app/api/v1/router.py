"""
API v1 router — aggregates all endpoint routers.

Phase 1 — Core CICS transaction → REST endpoint mapping:
  CC00 (COSGN00C) → POST /api/v1/auth/login
  CA0V (COACTVWC) → GET  /api/v1/accounts/{id}
  CA0U (COACTUPC) → PUT  /api/v1/accounts/{id}
  CC0L (COCRDLIC) → GET  /api/v1/cards
  CC0S (COCRDSLC) → GET  /api/v1/cards/{card_num}
  CC0U (COCRDUPC) → PUT  /api/v1/cards/{card_num}
  CT00 (COTRN00C) → GET  /api/v1/transactions
  CT01 (COTRN01C) → GET  /api/v1/transactions/{id}
  CT02 (COTRN02C) → POST /api/v1/transactions
  CB00 (COBIL00C) → POST /api/v1/transactions/payment
  CU00 (COUSR00C) → GET  /api/v1/admin/users
  CU01 (COUSR01C) → POST /api/v1/admin/users
  CU02 (COUSR02C) → PUT  /api/v1/admin/users/{id}
  CU03 (COUSR03C) → DELETE /api/v1/admin/users/{id}

Phase 2 — Financial Operations:
  CB00 (COBIL00C) → POST /api/v1/accounts/{id}/payments    (bill payment)
  CR00 (CORPT00C) → POST /api/v1/reports/transactions      (report submission)
  CA00 (COADM01C) → GET  /api/v1/admin/menu                (admin menu metadata)
  CTLI (COTRTLIC) → GET  /api/v1/transaction-types         (transaction type list)
  CTTU (COTRTUPC) → PUT  /api/v1/transaction-types/{id}    (transaction type update)

Phase 3 — Authorization Module (MQ/IMS/DB2 → REST/PostgreSQL):
  CP00 (COPAUA0C) → POST /api/v1/authorizations                         (auth decision)
  CPVS (COPAUS0C) → GET  /api/v1/authorizations/accounts/{acct_id}      (summary list)
  CPVD (COPAUS1C) → GET  /api/v1/authorizations/details/{auth_id}        (detail view)
  CPVD (COPAUS1C) → GET  /api/v1/authorizations/accounts/{acct_id}/next  (PF8 navigate)
  PF5  (COPAUS2C) → POST /api/v1/authorizations/details/{auth_id}/fraud  (fraud mark)
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    accounts,
    admin,
    auth,
    authorizations,
    cards,
    reports,
    transaction_types,
    transactions,
    users,
)

api_router = APIRouter()

# Phase 1 routers
api_router.include_router(auth.router)
api_router.include_router(accounts.router)
api_router.include_router(cards.router)
api_router.include_router(transactions.router)
api_router.include_router(users.router)

# Phase 2 routers
api_router.include_router(reports.router)
api_router.include_router(admin.router)
api_router.include_router(transaction_types.router)

# Phase 3 routers — Authorization module
api_router.include_router(authorizations.router)
