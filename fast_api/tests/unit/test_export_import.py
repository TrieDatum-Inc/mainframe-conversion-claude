"""Unit tests for ExportImportService (CBEXPORT/CBIMPORT).

Tests:
- Export produces all 5 entity types in correct order
- Export counts match DB records
- Import validates referential integrity (3000-VALIDATE-IMPORT implementation)
- Import routes records to correct tables
- Import validation errors reported but processing continues
"""

import pytest

from app.models.account import Account
from app.models.card import Card
from app.models.card_cross_reference import CardCrossReference
from app.models.customer import Customer
from app.models.transaction import Transaction
from app.schemas.batch import (
    AccountExport,
    CardExport,
    CustomerExport,
    ExportPayload,
    TransactionExport,
    XrefExport,
)
from app.services.export_import import ExportImportService


def make_customer_export(cust_id: str = "000000001") -> CustomerExport:
    return CustomerExport(
        cust_id=cust_id,
        cust_first_name="Alice",
        cust_middle_name=None,
        cust_last_name="Test",
        cust_addr_line_1="123 Main St",
        cust_addr_line_2=None,
        cust_addr_line_3=None,
        cust_addr_state_cd="CA",
        cust_addr_country_cd="USA",
        cust_addr_zip="90210",
        cust_phone_num_1="555-1234",
        cust_phone_num_2=None,
        cust_ssn="123456789",
        cust_govt_issued_id=None,
        cust_dob=None,
        cust_eft_account_id=None,
        cust_pri_card_holder_ind="Y",
        cust_fico_credit_score=750,
    )


def make_export_payload(**kwargs) -> ExportPayload:
    defaults = dict(
        export_timestamp="2026-04-03 12:00:00.00",
        branch_id="0001",
        region_code="NORTH",
        customers=[make_customer_export()],
        accounts=[],
        xrefs=[],
        transactions=[],
        cards=[],
        total_records=1,
    )
    defaults.update(kwargs)
    return ExportPayload(**defaults)


class TestExportService:
    """Tests for CBEXPORT functionality."""

    @pytest.mark.asyncio
    async def test_export_returns_all_entities(
        self,
        db_session,
        sample_account,
        sample_xref,
    ):
        """Export fetches data from all 5 entity tables."""
        # Add a customer
        customer = Customer(
            cust_id="000000001",
            cust_first_name="Alice",
            cust_last_name="Test",
        )
        db_session.add(customer)

        # Add a card
        import datetime
        card = Card(
            card_num="4111111111111111",
            card_acct_id=sample_account.acct_id,
            card_expiration_date=datetime.date(2027, 12, 31),
            card_active_status="Y",
        )
        db_session.add(card)
        await db_session.flush()

        service = ExportImportService(db_session)
        result = await service.export_all()

        assert result["customers_exported"] == 1
        assert result["accounts_exported"] == 1
        assert result["xrefs_exported"] == 1
        assert result["cards_exported"] == 1
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_export_payload_has_correct_structure(
        self,
        db_session,
        sample_account,
        sample_xref,
    ):
        """Export payload contains all required fields."""
        service = ExportImportService(db_session)
        result = await service.export_all()

        payload = result["payload"]
        assert payload.branch_id == "0001"
        assert payload.region_code == "NORTH"
        assert isinstance(payload.export_timestamp, str)
        assert len(payload.accounts) == 1
        assert payload.accounts[0].acct_id == sample_account.acct_id

    @pytest.mark.asyncio
    async def test_export_empty_db_returns_zeros(self, db_session):
        """Export of empty database returns zero counts."""
        service = ExportImportService(db_session)
        result = await service.export_all()

        assert result["customers_exported"] == 0
        assert result["accounts_exported"] == 0
        assert result["total_records_exported"] == 0


class TestImportService:
    """Tests for CBIMPORT functionality."""

    @pytest.mark.asyncio
    async def test_import_customers_inserted(self, db_session):
        """Customer records from payload are inserted."""
        from sqlalchemy import select
        payload = make_export_payload(
            customers=[make_customer_export("000000001")],
            total_records=1,
        )
        service = ExportImportService(db_session)
        result = await service.import_data(payload)

        assert result["customers_imported"] == 1
        assert result["status"] == "completed"

        db_result = await db_session.execute(
            select(Customer).where(Customer.cust_id == "000000001")
        )
        cust = db_result.scalar_one_or_none()
        assert cust is not None
        assert cust.cust_first_name == "Alice"

    @pytest.mark.asyncio
    async def test_import_validates_xref_account_consistency(self, db_session):
        """Xref referencing account not in payload generates validation error."""
        payload = make_export_payload(
            accounts=[],  # No accounts
            xrefs=[XrefExport(
                xref_card_num="4111111111111111",
                xref_cust_id="000000001",
                xref_acct_id="00000000001",  # Not in payload accounts
            )],
            total_records=1,
        )
        service = ExportImportService(db_session)
        result = await service.import_data(payload)

        # Should have validation errors but still proceed
        assert result["error_count"] > 0
        validation_errors = result["validation_errors"]
        assert any(e.field == "xref_acct_id" for e in validation_errors)

    @pytest.mark.asyncio
    async def test_import_validates_card_account_consistency(self, db_session):
        """Card referencing account not in payload generates validation error."""
        payload = make_export_payload(
            accounts=[],  # No accounts
            cards=[CardExport(
                card_num="4111111111111111",
                card_acct_id="00000000001",  # Not in payload
                card_cvv_cd="123",
                card_embossed_name="TEST",
                card_expiration_date=None,
                card_active_status="Y",
            )],
            total_records=1,
        )
        service = ExportImportService(db_session)
        result = await service.import_data(payload)

        assert result["error_count"] > 0
        assert any(e.record_type == "D" for e in result["validation_errors"])

    @pytest.mark.asyncio
    async def test_import_validates_card_active_status(self, db_session):
        """Card with invalid active status generates validation error."""
        payload = make_export_payload(
            cards=[CardExport(
                card_num="4111111111111111",
                card_acct_id=None,
                card_cvv_cd="123",
                card_embossed_name="TEST",
                card_expiration_date=None,
                card_active_status="X",  # Invalid value
            )],
            total_records=1,
        )
        service = ExportImportService(db_session)
        result = await service.import_data(payload)

        assert result["error_count"] > 0
        assert any(e.field == "card_active_status" for e in result["validation_errors"])

    @pytest.mark.asyncio
    async def test_import_idempotent_on_duplicate(self, db_session):
        """Re-importing same data is idempotent (upsert behavior)."""
        from sqlalchemy import select
        payload = make_export_payload(
            customers=[make_customer_export()],
            total_records=1,
        )
        service = ExportImportService(db_session)

        # Import twice
        await service.import_data(payload)
        await service.import_data(payload)

        # Should still only have one record
        result = await db_session.execute(select(Customer))
        customers = result.scalars().all()
        assert len(customers) == 1
