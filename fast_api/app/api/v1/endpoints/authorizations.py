"""
Authorization endpoints — derived from COPAUA0C, COPAUS0C, COPAUS1C, COPAUS2C.

Source programs:
  app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl — CP00 transaction (authorization engine)
  app-authorization-ims-db2-mq/cbl/COPAUS0C.cbl — CPVS transaction (summary list view)
  app-authorization-ims-db2-mq/cbl/COPAUS1C.cbl — CPVD transaction (detail view)
  app-authorization-ims-db2-mq/cbl/COPAUS2C.cbl — Fraud sub-program (EXEC CICS LINK)

CICS transaction → REST endpoint mapping:
  CP00  POST /api/v1/authorizations                          — process_authorization
  CPVS  GET  /api/v1/authorizations/accounts/{acct_id}      — list_authorizations
  CPVD  GET  /api/v1/authorizations/details/{auth_id}        — get_authorization_detail
  CPVD  GET  /api/v1/authorizations/accounts/{acct_id}/next  — get_next_detail (PF8)
  PF5   POST /api/v1/authorizations/details/{auth_id}/fraud  — mark_fraud

MQ replacement note:
  The original COPAUA0C used IBM MQ (MQOPEN/MQGET/MQPUT1) for async request/reply.
  This is replaced by a synchronous REST POST. No MQ broker is required.
  The MQ W01-GET-BUFFER CSV payload maps to AuthorizationRequest JSON body.
  The MQ W02-PUT-BUFFER CSV response maps to AuthorizationResponse JSON body.
"""
from fastapi import APIRouter, Query

from app.dependencies import CurrentUser, DBSession
from app.schemas.authorization import (
    AuthDetailListResponse,
    AuthDetailResponse,
    AuthorizationRequest,
    AuthorizationResponse,
    FraudMarkRequest,
    FraudMarkResponse,
)
from app.services.authorization_service import AuthorizationService

router = APIRouter(prefix="/authorizations", tags=["Authorizations (COPAUA0C/COPAUS0C/COPAUS1C/COPAUS2C)"])


@router.post(
    "",
    response_model=AuthorizationResponse,
    status_code=200,
    summary="Process card authorization (COPAUA0C / CP00)",
    responses={
        200: {"description": "Authorization decision (approved or declined)"},
        422: {"description": "Invalid request payload"},
    },
)
async def process_authorization(
    request: AuthorizationRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> AuthorizationResponse:
    """
    Process a credit card authorization request.

    Replaces COPAUA0C (CICS transaction CP00) MQ-driven authorization engine.

    Original flow:
      1. EXEC CICS RETRIEVE INTO(MQTM) — receive MQ trigger message
      2. MQOPEN  — open request queue
      3. MQGET   — read CSV authorization request from queue
      4. UNSTRING W01-GET-BUFFER — parse CSV into PA-RQ-* fields
      5. EXEC CICS READ FILE(CCXREF)  — look up card → account
      6. EXEC CICS READ FILE(ACCTDAT) — read account record
      7. EXEC CICS READ FILE(CUSTDAT) — read customer record
      8. EXEC DLI GU SEGMENT(PAUTSUM0) — read auth summary from IMS
      9. 6000-MAKE-DECISION — credit limit check → approve or decline
      10. MQPUT1 — write CSV response to reply queue
      11. EXEC DLI REPL/ISRT SEGMENT(PAUTSUM0) — update IMS summary
      12. EXEC DLI ISRT SEGMENT(PAUTDTL1) — insert IMS detail record

    This endpoint performs steps 5-12 synchronously and returns the
    authorization decision that the MQ reply would have carried.

    Business rules (from 6000-MAKE-DECISION):
    - Card not in CCXREF → DECLINED, reason 3100 (INVALID CARD)
    - Account not found  → DECLINED, reason 3100
    - Account inactive   → DECLINED, reason 4300 (ACCOUNT CLOSED)
    - Amount > available credit → DECLINED, reason 4100 (INSUFFICIENT FUND)
    - Otherwise → APPROVED, approved_amt = transaction_amt
    """
    service = AuthorizationService(db)
    return await service.process_authorization(request)


@router.get(
    "/accounts/{acct_id}",
    response_model=AuthDetailListResponse,
    summary="List authorization history for account (COPAUS0C / CPVS)",
    responses={
        200: {"description": "Paginated authorization list with summary"},
        404: {"description": "Account not found"},
    },
)
async def list_authorizations(
    acct_id: int,
    db: DBSession,
    current_user: CurrentUser,
    cursor: int | None = Query(None, description="Keyset cursor — last auth_id from previous page (PF8 equivalent)"),
    limit: int = Query(5, ge=1, le=100, description="Page size (COPAUS0C: 5 rows per screen)"),
) -> AuthDetailListResponse:
    """
    List authorization records for an account with keyset pagination.

    Derived from COPAUS0C (CICS transaction CPVS) GATHER-DETAILS +
    PROCESS-PAGE-FORWARD paragraphs.

    COPAUS0C pagination model:
      CDEMO-CPVS-PAUKEY-PREV-PG OCCURS 20 TIMES — prev page keys
      CDEMO-CPVS-PAUKEY-LAST                    — next page key
      PF7 → PROCESS-PF7-KEY (previous page)
      PF8 → PROCESS-PF8-KEY (next page)

    Equivalent here:
      GET /api/v1/authorizations/accounts/{acct_id}?cursor=<last_auth_id>
      next_cursor in response = next page cursor (equivalent to PF8)
      prev_cursor in response = previous page cursor (equivalent to PF7)
    """
    service = AuthorizationService(db)
    return await service.list_authorizations(acct_id=acct_id, cursor=cursor, limit=limit)


@router.get(
    "/details/{auth_id}",
    response_model=AuthDetailResponse,
    summary="View authorization detail (COPAUS1C / CPVD)",
    responses={
        200: {"description": "Authorization detail record"},
        404: {"description": "Authorization not found (IMS GE = SEGMENT-NOT-FOUND)"},
    },
)
async def get_authorization_detail(
    auth_id: int,
    db: DBSession,
    current_user: CurrentUser,
) -> AuthDetailResponse:
    """
    Retrieve a single authorization detail record.

    Derived from COPAUS1C (CICS transaction CPVD) READ-AUTH-RECORD /
    PROCESS-ENTER-KEY paragraphs.

    COPAUS1C: EXEC DLI GU SEGMENT(PAUTSUM0/PAUTDTL1)
              WHERE (ACCNTID = PA-ACCT-ID) AND key = WS-AUTH-KEY
    Maps to: GET /api/v1/authorizations/details/{auth_id}

    Raises HTTP 404 when IMS returns 'GE' (SEGMENT-NOT-FOUND).
    """
    service = AuthorizationService(db)
    return await service.get_authorization_detail(auth_id)


@router.get(
    "/accounts/{acct_id}/next",
    response_model=AuthDetailResponse,
    summary="Navigate to next authorization (COPAUS1C PF8 / CPVD)",
    responses={
        200: {"description": "Next authorization detail record"},
        404: {"description": "Already at last authorization (IMS GB = end-of-db)"},
    },
)
async def get_next_authorization(
    acct_id: int,
    db: DBSession,
    current_user: CurrentUser,
    current_auth_id: int = Query(
        ..., description="Current auth_id — returns the next record after this one"
    ),
) -> AuthDetailResponse:
    """
    Navigate to the next authorization record for an account.

    Derived from COPAUS1C PROCESS-PF8-KEY → READ-NEXT-AUTH-RECORD:
      EXEC DLI GN (IMS get-next) on PAUTDTL1 child segments.

    HTTP 404 maps to AUTHS-EOF condition:
      COPAUS1C: 'Already at the last Authorization...' message.
    """
    service = AuthorizationService(db)
    return await service.get_next_authorization_detail(acct_id, current_auth_id)


@router.post(
    "/details/{auth_id}/fraud",
    response_model=FraudMarkResponse,
    summary="Mark/unmark authorization as fraud (COPAUS1C PF5 → COPAUS2C)",
    responses={
        200: {"description": "Fraud flag updated"},
        404: {"description": "Authorization not found"},
        500: {"description": "Database error (SQLCODE != 0 in COPAUS2C)"},
    },
)
async def mark_authorization_fraud(
    auth_id: int,
    request: FraudMarkRequest,
    db: DBSession,
    current_user: CurrentUser,
    acct_id: int = Query(..., description="Account ID (WS-ACCT-ID passed in COMMAREA)"),
    cust_id: int = Query(..., description="Customer ID (CDEMO-CUST-ID passed in COMMAREA)"),
) -> FraudMarkResponse:
    """
    Mark or unmark an authorization as fraudulent.

    Derived from COPAUS1C MARK-AUTH-FRAUD paragraph (PF5 key):

      IF PA-FRAUD-CONFIRMED:
        SET PA-FRAUD-REMOVED   → action='R'  (remove fraud flag)
      ELSE:
        SET PA-FRAUD-CONFIRMED → action='F'  (report as fraud)

      EXEC CICS LINK PROGRAM(COPAUS2C) COMMAREA(WS-FRAUD-DATA)

    COPAUS2C then executes:
      EXEC SQL INSERT INTO CARDDEMO.AUTHFRDS (...)
      IF SQLCODE = -803 → PERFORM FRAUD-UPDATE (UPDATE ... SET AUTH_FRAUD=...)

    On success: auth_details row is updated (EXEC DLI REPL SEGMENT(PAUTDTL1)).
    On failure: original COBOL performs ROLL-BACK and shows error message.
                This API returns the error in the response body (success=false).

    Note: The COBOL toggle is caller-driven here — the client decides
    whether to send action='F' or action='R'. The COPAUS1C toggle logic
    is: check existing auth_fraud field, flip it. The caller should
    first read the detail record (GET /details/{auth_id}) to determine
    the current fraud state before deciding which action to submit.
    """
    service = AuthorizationService(db)
    return await service.mark_fraud(
        auth_id=auth_id,
        acct_id=acct_id,
        cust_id=cust_id,
        request=request,
    )
