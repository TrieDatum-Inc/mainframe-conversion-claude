"""
Unit tests for TransactionTypeService — business logic from COTRTLIC and COTRTUPC.

Tests verify all business rules:
  1. list_transaction_types — cursor pagination (C-TR-TYPE-FORWARD/BACKWARD cursors)
  2. get_transaction_type — SQLCODE=100 → RecordNotFoundError
  3. update_transaction_type — description validation, no-change detection
  4. create_transaction_type — type_cd validation (numeric, non-zero, max 2 digits)
  5. delete_transaction_type — record must exist
  6. Page size limit = 7 (COTRTLIC WS-MAX-SCREEN-LINES)
"""
from decimal import Decimal

import pytest

from app.models.transaction import TransactionType
from app.schemas.transaction_type import TransactionTypeUpdateRequest
from app.services.transaction_type_service import MAX_PAGE_SIZE, TransactionTypeService
from app.utils.error_handlers import RecordNotFoundError, ValidationError


class TestTransactionTypeService:
    """Tests for COTRTLIC / COTRTUPC business logic."""

    @pytest.mark.asyncio
    async def test_list_returns_paginated_items(
        self, db, tran_type: TransactionType
    ) -> None:
        """
        COTRTLIC C-TR-TYPE-FORWARD cursor: returns rows ordered by TR_TYPE.
        """
        service = TransactionTypeService(db)
        result = await service.list_transaction_types(limit=7)

        assert result.total >= 1
        assert len(result.items) >= 1

    @pytest.mark.asyncio
    async def test_list_page_size_capped_at_max(
        self, db, tran_type: TransactionType
    ) -> None:
        """
        COTRTLIC WS-MAX-SCREEN-LINES = 7.
        Result items must not exceed MAX_PAGE_SIZE rows.
        """
        service = TransactionTypeService(db)
        result = await service.list_transaction_types(limit=100)  # request more than max

        assert len(result.items) <= MAX_PAGE_SIZE

    @pytest.mark.asyncio
    async def test_list_filter_by_type_cd(
        self, db, tran_type: TransactionType
    ) -> None:
        """
        COTRTLIC: WS-EDIT-TYPE-FLAG='1' → AND TR_TYPE = :WS-TYPE-CD-FILTER
        Type code filter returns only matching record.
        """
        service = TransactionTypeService(db)
        result = await service.list_transaction_types(type_cd_filter="01")

        assert all(item.type_cd == "01" for item in result.items)

    @pytest.mark.asyncio
    async def test_get_existing_type(self, db, tran_type: TransactionType) -> None:
        """
        COTRTUPC 9000-READ-TRANTYPE: SELECT ... WHERE TR_TYPE = :key
        Existing type returns correct record.
        """
        service = TransactionTypeService(db)
        result = await service.get_transaction_type("01")

        assert result.type_cd == "01"
        assert result.description == "Purchase"

    @pytest.mark.asyncio
    async def test_get_nonexistent_type_raises(self, db) -> None:
        """
        COTRTUPC 9000-READ-TRANTYPE: SQLCODE=100 → RecordNotFoundError.
        'No record found for this key in database'
        """
        service = TransactionTypeService(db)
        with pytest.raises(RecordNotFoundError):
            await service.get_transaction_type("99")

    @pytest.mark.asyncio
    async def test_update_description_succeeds(self, db, tran_type: TransactionType) -> None:
        """
        COTRTUPC 9600-WRITE-PROCESSING:
          UPDATE CARDDEMO.TRANSACTION_TYPE SET TR_DESCRIPTION = :new WHERE TR_TYPE = :key
        """
        service = TransactionTypeService(db)
        request = TransactionTypeUpdateRequest(description="Credit Purchase")
        result = await service.update_transaction_type("01", request)

        assert result.type_cd == "01"
        assert result.description == "Credit Purchase"

    @pytest.mark.asyncio
    async def test_update_no_change_returns_unchanged(self, db, tran_type: TransactionType) -> None:
        """
        COTRTUPC 1205-COMPARE-OLD-NEW:
          IF FUNCTION UPPER-CASE(TTUP-NEW-TTYP-TYPE-DESC) = FUNCTION UPPER-CASE(TTUP-OLD-TTYP-TYPE-DESC)
          → SET NO-CHANGES-DETECTED TO TRUE
        No actual DB update when description unchanged (case-insensitive).
        """
        service = TransactionTypeService(db)
        request = TransactionTypeUpdateRequest(description="PURCHASE")  # same as "Purchase" uppercased
        result = await service.update_transaction_type("01", request)

        # Should return the record (no error raised for no-change)
        assert result.type_cd == "01"

    @pytest.mark.asyncio
    async def test_update_nonexistent_type_raises(self, db) -> None:
        """RecordNotFoundError when type_cd does not exist."""
        service = TransactionTypeService(db)
        request = TransactionTypeUpdateRequest(description="Some Desc")
        with pytest.raises(RecordNotFoundError):
            await service.update_transaction_type("99", request)

    @pytest.mark.asyncio
    async def test_create_valid_type_succeeds(self, db) -> None:
        """
        COTRTUPC TTUP-CREATE-NEW-RECORD:
          INSERT INTO CARDDEMO.TRANSACTION_TYPE (TR_TYPE, TR_DESCRIPTION)
        """
        service = TransactionTypeService(db)
        result = await service.create_transaction_type("05", "Refund")

        assert result.type_cd == "05"
        assert result.description == "Refund"

    def test_validate_type_cd_blank_raises(self) -> None:
        """
        COTRTUPC 1245-EDIT-NUM-REQD:
          IF WS-EDIT-ALPHANUM-ONLY EQUAL SPACES → 'Tran Type code must be supplied.'
        """
        with pytest.raises(ValidationError, match="must be supplied"):
            TransactionTypeService._validate_type_cd("   ")

    def test_validate_type_cd_non_numeric_raises(self) -> None:
        """
        COTRTUPC 1245-EDIT-NUM-REQD:
          IF FUNCTION TEST-NUMVAL(...) != 0 → 'Tran Type code must be numeric.'
        """
        with pytest.raises(ValidationError, match="numeric"):
            TransactionTypeService._validate_type_cd("AB")

    def test_validate_type_cd_zero_raises(self) -> None:
        """
        COTRTUPC 1245-EDIT-NUM-REQD:
          IF FUNCTION NUMVAL(...) = 0 → 'Tran Type code must not be zero.'
        """
        with pytest.raises(ValidationError, match="not be zero"):
            TransactionTypeService._validate_type_cd("00")

    def test_validate_type_cd_too_long_raises(self) -> None:
        """TR_TYPE is CHAR(2) — max 2 digits."""
        with pytest.raises(ValidationError, match="max 2"):
            TransactionTypeService._validate_type_cd("123")

    def test_validate_type_cd_single_digit_ok(self) -> None:
        """Single-digit type codes are valid (zero-padded to '01')."""
        # Should not raise
        TransactionTypeService._validate_type_cd("1")

    def test_validate_type_cd_two_digits_ok(self) -> None:
        """Two-digit non-zero numeric type codes are valid."""
        TransactionTypeService._validate_type_cd("12")

    @pytest.mark.asyncio
    async def test_delete_existing_type_succeeds(self, db, tran_type: TransactionType) -> None:
        """
        COTRTLIC 9300-DELETE-RECORD:
          DELETE FROM CARDDEMO.TRANSACTION_TYPE WHERE TR_TYPE IN (...)
        Delete existing record succeeds without error.
        """
        service = TransactionTypeService(db)
        # Should not raise
        await service.delete_transaction_type("01")

    @pytest.mark.asyncio
    async def test_delete_nonexistent_type_raises(self, db) -> None:
        """
        COTRTLIC 9300-DELETE-RECORD: FLG-DELETED-NO → 'Delete of record failed'.
        Delete of nonexistent record raises RecordNotFoundError.
        """
        service = TransactionTypeService(db)
        with pytest.raises(RecordNotFoundError):
            await service.delete_transaction_type("99")


class TestTransactionTypeSchemaValidation:
    """Tests for COTRTUPC 1230-EDIT-ALPHANUM-REQD validation rules in schema."""

    def test_description_blank_raises(self) -> None:
        """
        COTRTUPC 1230-EDIT-ALPHANUM-REQD:
          IF WS-EDIT-ALPHANUM-ONLY EQUAL SPACES → 'must be supplied.'
        """
        with pytest.raises(ValueError, match="blank"):
            TransactionTypeUpdateRequest(description="   ")

    def test_description_special_chars_raises(self) -> None:
        """
        COTRTUPC 1230-EDIT-ALPHANUM-REQD:
          INSPECT ... CONVERTING LIT-ALL-ALPHANUM-FROM TO LIT-ALPHANUM-SPACES-TO
          → non-alphanumeric chars (except space) rejected.
        """
        with pytest.raises(ValueError, match="alphabets"):
            TransactionTypeUpdateRequest(description="Bad!@#Desc")

    def test_description_alphanumeric_ok(self) -> None:
        """Alphanumeric + spaces pass COTRTUPC 1230-EDIT-ALPHANUM-REQD."""
        req = TransactionTypeUpdateRequest(description="Valid Desc 123")
        assert req.description == "Valid Desc 123"

    def test_description_max_50_chars(self) -> None:
        """TR_DESCRIPTION CHAR(50) — descriptions up to 50 chars are valid."""
        long_desc = "A" * 50
        req = TransactionTypeUpdateRequest(description=long_desc)
        assert len(req.description) == 50

    def test_description_over_50_chars_rejected(self) -> None:
        """TR_DESCRIPTION CHAR(50) — descriptions over 50 chars are rejected by Pydantic."""
        with pytest.raises(ValueError):
            TransactionTypeUpdateRequest(description="A" * 51)
