"""
Integration tests for /api/v1/transaction-types (COTRTLIC/COTRTUPC / CTLI/CTTU).

Tests verify HTTP-level behavior:
  1. GET /api/v1/transaction-types — paginated list (C-TR-TYPE-FORWARD cursor)
  2. GET /api/v1/transaction-types/{type_cd} — single type detail
  3. PUT /api/v1/transaction-types/{type_cd} — update description
  4. POST /api/v1/transaction-types — create new type
  5. DELETE /api/v1/transaction-types/{type_cd} — delete record
  6. All endpoints require admin access
  7. 404 for missing records, 422 for validation errors
"""
import pytest
from httpx import AsyncClient

from app.models.transaction import TransactionType


class TestTransactionTypesListEndpoint:
    """Tests for COTRTLIC C-TR-TYPE-FORWARD cursor browse."""

    @pytest.mark.asyncio
    async def test_list_returns_200(
        self, client: AsyncClient, auth_token: str, tran_type: TransactionType
    ) -> None:
        """COTRTLIC: list transaction types returns 200 with items."""
        response = await client.get(
            "/api/v1/transaction-types",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_response_structure(
        self, client: AsyncClient, auth_token: str, tran_type: TransactionType
    ) -> None:
        """Response has items, total, next_cursor, prev_cursor fields."""
        response = await client.get(
            "/api/v1/transaction-types",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "next_cursor" in data
        assert "prev_cursor" in data

    @pytest.mark.asyncio
    async def test_list_items_have_correct_fields(
        self, client: AsyncClient, auth_token: str, tran_type: TransactionType
    ) -> None:
        """
        COTRTLIC: each row has TR_TYPE and TR_DESCRIPTION.
        (TRTTYPO PIC X(02) and TRTYPDO PIC X(50))
        """
        response = await client.get(
            "/api/v1/transaction-types",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        for item in data["items"]:
            assert "type_cd" in item
            assert "description" in item

    @pytest.mark.asyncio
    async def test_list_filter_by_type_cd(
        self, client: AsyncClient, auth_token: str, tran_type: TransactionType
    ) -> None:
        """
        COTRTLIC: WS-EDIT-TYPE-FLAG='1' → exact TR_TYPE match.
        """
        response = await client.get(
            "/api/v1/transaction-types?type_cd=01",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        assert all(item["type_cd"] == "01" for item in data["items"])

    @pytest.mark.asyncio
    async def test_list_requires_admin(
        self, client: AsyncClient, user_token: str
    ) -> None:
        """COTRTLIC is admin-only (COADM01C dispatches it)."""
        response = await client.get(
            "/api/v1/transaction-types",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_unauthorized_without_token(self, client: AsyncClient) -> None:
        """Unauthenticated → 401."""
        response = await client.get("/api/v1/transaction-types")
        assert response.status_code == 401


class TestTransactionTypeDetailEndpoint:
    """Tests for COTRTUPC 9000-READ-TRANTYPE detail retrieval."""

    @pytest.mark.asyncio
    async def test_get_existing_type_returns_200(
        self, client: AsyncClient, auth_token: str, tran_type: TransactionType
    ) -> None:
        """
        COTRTUPC 9000-READ-TRANTYPE: SELECT ... WHERE TR_TYPE = '01' → 200 OK.
        """
        response = await client.get(
            "/api/v1/transaction-types/01",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_existing_type_body(
        self, client: AsyncClient, auth_token: str, tran_type: TransactionType
    ) -> None:
        """Response body contains correct TR_TYPE and TR_DESCRIPTION."""
        response = await client.get(
            "/api/v1/transaction-types/01",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        assert data["type_cd"] == "01"
        assert data["description"] == "Purchase"

    @pytest.mark.asyncio
    async def test_get_nonexistent_type_returns_404(
        self, client: AsyncClient, auth_token: str
    ) -> None:
        """
        COTRTUPC 9000-READ-TRANTYPE: SQLCODE=100 → 'No record found' → HTTP 404.
        """
        response = await client.get(
            "/api/v1/transaction-types/99",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 404


class TestTransactionTypeUpdateEndpoint:
    """Tests for COTRTUPC 9600-WRITE-PROCESSING UPDATE."""

    @pytest.mark.asyncio
    async def test_update_description_returns_200(
        self, client: AsyncClient, auth_token: str, tran_type: TransactionType
    ) -> None:
        """
        COTRTUPC 9600-WRITE-PROCESSING:
          UPDATE CARDDEMO.TRANSACTION_TYPE SET TR_DESCRIPTION=... WHERE TR_TYPE=...
        → 200 OK.
        """
        response = await client.put(
            "/api/v1/transaction-types/01",
            json={"description": "Credit Purchase"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_reflects_new_description(
        self, client: AsyncClient, auth_token: str, tran_type: TransactionType
    ) -> None:
        """Updated description is reflected in response body."""
        await client.put(
            "/api/v1/transaction-types/01",
            json={"description": "Retail Purchase"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        verify = await client.get(
            "/api/v1/transaction-types/01",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert verify.json()["description"] == "Retail Purchase"

    @pytest.mark.asyncio
    async def test_update_blank_description_returns_422(
        self, client: AsyncClient, auth_token: str, tran_type: TransactionType
    ) -> None:
        """
        COTRTUPC 1230-EDIT-ALPHANUM-REQD:
          IF WS-EDIT-ALPHANUM-ONLY EQUAL SPACES → error.
        """
        response = await client.put(
            "/api/v1/transaction-types/01",
            json={"description": "   "},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_special_chars_in_description_returns_422(
        self, client: AsyncClient, auth_token: str, tran_type: TransactionType
    ) -> None:
        """
        COTRTUPC 1230-EDIT-ALPHANUM-REQD:
          INSPECT ... non-alphanumeric chars rejected.
        """
        response = await client.put(
            "/api/v1/transaction-types/01",
            json={"description": "Bad!@#Desc"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_nonexistent_type_returns_404(
        self, client: AsyncClient, auth_token: str
    ) -> None:
        """COTRTUPC: record not found before update → 404."""
        response = await client.put(
            "/api/v1/transaction-types/99",
            json={"description": "Some Description"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_requires_admin(
        self, client: AsyncClient, user_token: str, tran_type: TransactionType
    ) -> None:
        """Non-admin cannot update transaction types."""
        response = await client.put(
            "/api/v1/transaction-types/01",
            json={"description": "New Desc"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403


class TestTransactionTypeDeleteEndpoint:
    """Tests for COTRTLIC 9300-DELETE-RECORD."""

    @pytest.mark.asyncio
    async def test_delete_existing_returns_204(
        self, client: AsyncClient, auth_token: str, tran_type: TransactionType
    ) -> None:
        """
        COTRTLIC 9300-DELETE-RECORD:
          DELETE ... WHERE TR_TYPE IN (...) → 204 No Content.
        """
        response = await client.delete(
            "/api/v1/transaction-types/02",  # '02' = Payment, safe to delete in test
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_404(
        self, client: AsyncClient, auth_token: str
    ) -> None:
        """COTRTLIC: FLG-DELETED-NO → 'Delete of record failed' → HTTP 404."""
        response = await client.delete(
            "/api/v1/transaction-types/99",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_requires_admin(
        self, client: AsyncClient, user_token: str, tran_type: TransactionType
    ) -> None:
        """Non-admin cannot delete transaction types."""
        response = await client.delete(
            "/api/v1/transaction-types/01",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403
