"""
Integration tests for the accounts API endpoints.

Tests the full HTTP request/response cycle:
  GET  /api/v1/accounts/{account_id}  → COACTVWC (Account View)
  PUT  /api/v1/accounts/{account_id}  → COACTUPC (Account Update)

COBOL origin:
  COACTVWC — Transaction CAVW; reads ACCTDAT + CUSTDAT via CXACAIX
  COACTUPC — Transaction CAUP; validates 15+ fields, REWRITEs ACCTDAT + CUSTDAT
"""

import pytest
from decimal import Decimal
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Shared request helpers
# ---------------------------------------------------------------------------

def _valid_update_body(customer_id: int = 100001) -> dict:
    """Build a valid AccountUpdateRequest body for test reuse."""
    return {
        "active_status": "Y",
        "open_date": "2020-01-15",
        "expiration_date": "2026-01-15",
        "reissue_date": "2024-01-15",
        "credit_limit": "5000.00",
        "cash_credit_limit": "1000.00",
        "current_balance": "250.00",
        "curr_cycle_credit": "0.00",
        "curr_cycle_debit": "250.00",
        "group_id": "GRP001",
        "customer": {
            "customer_id": customer_id,
            "first_name": "Alice",
            "middle_name": "B",
            "last_name": "Smith",
            "address_line_1": "123 Main St",
            "address_line_2": None,
            "city": "Springfield",
            "state_code": "IL",
            "zip_code": "62701",
            "country_code": "USA",
            "phone_1": "217-555-1234",
            "phone_2": None,
            "ssn_part1": "123",
            "ssn_part2": "45",
            "ssn_part3": "6789",
            "date_of_birth": "1985-06-15",
            "fico_score": 720,
            "government_id_ref": "DL-IL-123456",
            "eft_account_id": "EFT0001",
            "primary_card_holder": "Y",
        },
    }


# ---------------------------------------------------------------------------
# GET /api/v1/accounts/{account_id}
# ---------------------------------------------------------------------------


class TestGetAccountEndpoint:
    """Tests for GET /api/v1/accounts/{account_id} (COACTVWC equivalent)."""

    @pytest.mark.asyncio
    async def test_get_account_success_returns_full_response(
        self, client: AsyncClient, seed_accounts, auth_token: str
    ):
        """
        Happy path: existing account returns 200 with full AccountViewResponse.

        COBOL origin: COACTVWC 9000-READ-ACCT paragraph — READ ACCTDAT + CUSTDAT.
        """
        response = await client.get(
            "/api/v1/accounts/10000000001",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["account_id"] == 10000000001
        assert data["active_status"] == "Y"
        assert "credit_limit" in data
        assert "customer" in data
        customer = data["customer"]
        assert customer["first_name"] == "Alice"
        assert customer["last_name"] == "Smith"

    @pytest.mark.asyncio
    async def test_get_account_ssn_is_masked(
        self, client: AsyncClient, seed_accounts, auth_token: str
    ):
        """
        SSN must always be masked in the response.

        SECURITY: COBOL stored full SSN in plain text (CUST-SSN 9(9)).
        Modern API returns only last 4 digits: ***-**-XXXX.
        """
        response = await client.get(
            "/api/v1/accounts/10000000001",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        ssn_masked = response.json()["customer"]["ssn_masked"]
        # Must not reveal first 5 SSN digits; must show last 4
        assert ssn_masked.startswith("***-**-")
        assert len(ssn_masked) == 11
        # Verify the raw SSN is not present anywhere in the response body
        assert "123-45-6789" not in response.text

    @pytest.mark.asyncio
    async def test_get_account_not_found_returns_404(
        self, client: AsyncClient, seed_accounts, auth_token: str
    ):
        """
        Non-existent account_id → 404 ACCOUNT_NOT_FOUND.

        COBOL origin: COACTVWC RESP=NOTFND on ACCTDAT read →
        DID-NOT-FIND-ACCT-IN-ACCTDAT message.
        """
        response = await client.get(
            "/api/v1/accounts/99999999999",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 404
        assert response.json()["error_code"] == "ACCOUNT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_get_account_unauthenticated_returns_4xx(
        self, client: AsyncClient, seed_accounts
    ):
        """
        No Authorization header → 4xx (403 from FastAPI HTTPBearer, or 401).

        COBOL origin: EIBCALEN=0 → XCTL COSGN00C (redirect to signon).
        FastAPI's HTTPBearer returns 403 when the Authorization header is
        absent entirely, and 401 when a token is present but invalid.
        Both signal "not authenticated" to the frontend.
        """
        response = await client.get("/api/v1/accounts/10000000001")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_get_account_invalid_token_returns_401(
        self, client: AsyncClient, seed_accounts
    ):
        """Invalid JWT → 401 UNAUTHORIZED."""
        response = await client.get(
            "/api/v1/accounts/10000000001",
            headers={"Authorization": "Bearer not.a.valid.jwt"},
        )
        assert response.status_code == 401
        assert response.json()["error_code"] == "UNAUTHORIZED"

    @pytest.mark.asyncio
    async def test_get_account_not_found_never_returns_customer_not_found_error_code(
        self, client: AsyncClient, seed_accounts, auth_token: str
    ):
        """
        404 response must never use CUSTOMER_NOT_FOUND error code.

        SEC-02: Returning distinct error codes for "account missing" vs
        "account exists but has no customer" would allow enumeration of
        which account IDs exist in the system. Both 404 paths must use
        the same ACCOUNT_NOT_FOUND code.
        """
        response = await client.get(
            "/api/v1/accounts/99999999999",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 404
        assert response.json()["error_code"] == "ACCOUNT_NOT_FOUND"
        assert "CUSTOMER_NOT_FOUND" not in response.text

    @pytest.mark.asyncio
    async def test_get_account_zero_id_returns_422(
        self, client: AsyncClient, seed_accounts, auth_token: str
    ):
        """
        account_id=0 → 422 INVALID_ACCOUNT_ID.

        COBOL origin: COACTVWC 2000-PROCESS-INPUTS — SEARCHED-ACCT-ZEROES
        validation: account ID must be non-zero.
        """
        response = await client.get(
            "/api/v1/accounts/0",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# PUT /api/v1/accounts/{account_id}
# ---------------------------------------------------------------------------


class TestUpdateAccountEndpoint:
    """Tests for PUT /api/v1/accounts/{account_id} (COACTUPC equivalent)."""

    @pytest.mark.asyncio
    async def test_update_account_success_returns_updated_data(
        self, client: AsyncClient, seed_accounts, auth_token: str
    ):
        """
        Happy path: valid update returns 200 with updated AccountViewResponse.

        COBOL origin: COACTUPC 9000-UPDATE-ACCOUNT — READ UPDATE + REWRITE.
        """
        body = _valid_update_body(customer_id=100001)
        body["group_id"] = "NEWGRP"  # change one field to ensure a diff

        response = await client.put(
            "/api/v1/accounts/10000000001",
            json=body,
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["account_id"] == 10000000001
        assert data["group_id"] == "NEWGRP"

    @pytest.mark.asyncio
    async def test_update_account_not_found_returns_404(
        self, client: AsyncClient, seed_accounts, auth_token: str
    ):
        """Non-existent account_id on PUT → 404 ACCOUNT_NOT_FOUND."""
        response = await client.put(
            "/api/v1/accounts/99999999999",
            json=_valid_update_body(),
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 404
        assert response.json()["error_code"] == "ACCOUNT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_update_account_unauthenticated_returns_4xx(
        self, client: AsyncClient, seed_accounts
    ):
        """No Authorization header on PUT → 4xx (403 from FastAPI HTTPBearer)."""
        response = await client.put(
            "/api/v1/accounts/10000000001",
            json=_valid_update_body(),
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_update_account_no_changes_returns_422(
        self, client: AsyncClient, seed_accounts, auth_token: str
    ):
        """
        All submitted fields identical to current values → 422 NO_CHANGES_DETECTED.

        COBOL origin: COACTUPC WS-DATACHANGED-FLAG='0' path — program only
        REWRITEs if at least one field was modified.
        """
        # First load the account to get current values
        get_resp = await client.get(
            "/api/v1/accounts/10000000001",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert get_resp.status_code == 200
        current = get_resp.json()

        # Build a PUT body that matches current values exactly
        body = {
            "active_status": current["active_status"],
            "open_date": current["open_date"],
            "expiration_date": current["expiration_date"],
            "reissue_date": current["reissue_date"],
            "credit_limit": current["credit_limit"],
            "cash_credit_limit": current["cash_credit_limit"],
            "current_balance": current["current_balance"],
            "curr_cycle_credit": current["curr_cycle_credit"],
            "curr_cycle_debit": current["curr_cycle_debit"],
            "group_id": current["group_id"],
            "customer": {
                "customer_id": current["customer"]["customer_id"],
                "first_name": current["customer"]["first_name"],
                "middle_name": current["customer"].get("middle_name"),
                "last_name": current["customer"]["last_name"],
                "address_line_1": current["customer"].get("address_line_1"),
                "address_line_2": current["customer"].get("address_line_2"),
                "city": current["customer"].get("city"),
                "state_code": current["customer"].get("state_code"),
                "zip_code": current["customer"].get("zip_code"),
                "country_code": current["customer"].get("country_code"),
                "phone_1": current["customer"].get("phone_1"),
                "phone_2": current["customer"].get("phone_2"),
                # SSN is masked in response; use original seed values for parts
                "ssn_part1": "123",
                "ssn_part2": "45",
                "ssn_part3": "6789",
                "date_of_birth": str(current["customer"].get("date_of_birth", "1985-06-15")),
                "fico_score": current["customer"].get("fico_score"),
                "government_id_ref": current["customer"].get("government_id_ref"),
                "eft_account_id": current["customer"].get("eft_account_id"),
                "primary_card_holder": current["customer"]["primary_card_holder"],
            },
        }

        response = await client.put(
            "/api/v1/accounts/10000000001",
            json=body,
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 422
        assert response.json()["error_code"] == "NO_CHANGES_DETECTED"

    @pytest.mark.asyncio
    async def test_update_account_invalid_ssn_part1_returns_422(
        self, client: AsyncClient, seed_accounts, auth_token: str
    ):
        """
        SSN part1 = 000 → 422 validation error.

        COBOL origin: COACTUPC INVALID-SSN-PART1 88-level — area code 000 invalid.
        """
        body = _valid_update_body()
        body["customer"]["ssn_part1"] = "000"

        response = await client.put(
            "/api/v1/accounts/10000000001",
            json=body,
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 422
        error_text = response.text
        assert "000" in error_text or "area number" in error_text or "invalid" in error_text.lower()

    @pytest.mark.asyncio
    async def test_update_account_ssn_part1_666_returns_422(
        self, client: AsyncClient, seed_accounts, auth_token: str
    ):
        """SSN part1 = 666 → 422 (IRS/SSA rule: 666 is never assigned)."""
        body = _valid_update_body()
        body["customer"]["ssn_part1"] = "666"

        response = await client.put(
            "/api/v1/accounts/10000000001",
            json=body,
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_account_ssn_part1_900_range_returns_422(
        self, client: AsyncClient, seed_accounts, auth_token: str
    ):
        """SSN part1 in 900-999 range → 422."""
        body = _valid_update_body()
        body["customer"]["ssn_part1"] = "900"

        response = await client.put(
            "/api/v1/accounts/10000000001",
            json=body,
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_account_cash_limit_exceeds_credit_returns_422(
        self, client: AsyncClient, seed_accounts, auth_token: str
    ):
        """
        cash_credit_limit > credit_limit → 422.

        COBOL origin: COACTUPC WS-EDIT-SIGNED-NUMBER-9V2-X — cash must be <= credit.
        Also enforced by DB constraint chk_accounts_cash_lte_credit.
        """
        body = _valid_update_body()
        body["credit_limit"] = "1000.00"
        body["cash_credit_limit"] = "2000.00"  # exceeds credit

        response = await client.put(
            "/api/v1/accounts/10000000001",
            json=body,
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_account_invalid_fico_below_300_returns_422(
        self, client: AsyncClient, seed_accounts, auth_token: str
    ):
        """
        FICO score < 300 → 422.

        COBOL origin: COACTUPC WS-EDIT-FICO-SCORE-FLGS — valid range is 300-850.
        """
        body = _valid_update_body()
        body["customer"]["fico_score"] = 250

        response = await client.put(
            "/api/v1/accounts/10000000001",
            json=body,
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_account_invalid_fico_above_850_returns_422(
        self, client: AsyncClient, seed_accounts, auth_token: str
    ):
        """FICO score > 850 → 422."""
        body = _valid_update_body()
        body["customer"]["fico_score"] = 900

        response = await client.put(
            "/api/v1/accounts/10000000001",
            json=body,
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_account_invalid_phone_format_returns_422(
        self, client: AsyncClient, seed_accounts, auth_token: str
    ):
        """
        Phone not matching NNN-NNN-NNNN → 422.

        COBOL origin: COACTUPC WS-EDIT-US-PHONE-NUM — three-segment validation
        (area code / exchange / subscriber).
        """
        body = _valid_update_body()
        body["customer"]["phone_1"] = "5551234"  # wrong format

        response = await client.put(
            "/api/v1/accounts/10000000001",
            json=body,
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_account_invalid_active_status_returns_422(
        self, client: AsyncClient, seed_accounts, auth_token: str
    ):
        """active_status not in ('Y', 'N') → 422."""
        body = _valid_update_body()
        body["active_status"] = "X"

        response = await client.put(
            "/api/v1/accounts/10000000001",
            json=body,
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_account_zero_id_returns_422(
        self, client: AsyncClient, seed_accounts, auth_token: str
    ):
        """
        account_id=0 on PUT → 422 INVALID_ACCOUNT_ID.

        SEC-03: PUT was missing the account_id > 0 guard present on GET.
        A zero or negative ID should be rejected before any DB access,
        returning 422 consistent with the GET endpoint behaviour.
        """
        response = await client.put(
            "/api/v1/accounts/0",
            json=_valid_update_body(),
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        # FastAPI Path(gt=0) rejects at the router layer with 422
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_account_not_found_returns_account_not_found_error_code(
        self, client: AsyncClient, seed_accounts, auth_token: str
    ):
        """
        Non-existent account_id on PUT → 404 with error_code ACCOUNT_NOT_FOUND,
        NOT CUSTOMER_NOT_FOUND.

        SEC-02: Both 404 paths (account missing, customer missing) must return
        the same error_code to prevent enumeration of which account IDs exist.
        """
        response = await client.put(
            "/api/v1/accounts/99999999999",
            json=_valid_update_body(),
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 404
        # Must be the generic ACCOUNT_NOT_FOUND, never CUSTOMER_NOT_FOUND
        assert response.json()["error_code"] == "ACCOUNT_NOT_FOUND"
        assert "CUSTOMER_NOT_FOUND" not in response.text

    @pytest.mark.asyncio
    async def test_update_account_response_has_masked_ssn(
        self, client: AsyncClient, seed_accounts, auth_token: str
    ):
        """
        After update, the response must still mask the SSN.

        SECURITY: Even after writing a new SSN, the API must never return it unmasked.
        """
        body = _valid_update_body()
        body["group_id"] = "CHANGED"  # ensure a change is made

        response = await client.put(
            "/api/v1/accounts/10000000001",
            json=body,
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        ssn_masked = response.json()["customer"]["ssn_masked"]
        assert ssn_masked.startswith("***-**-")
        # Submitted SSN (123-45-6789) must not appear in response
        assert "123-45-6789" not in response.text
