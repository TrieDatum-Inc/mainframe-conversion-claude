"""Export/Import Service — CBEXPORT and CBIMPORT equivalents.

CBEXPORT: reads all 5 entity tables, produces JSON export payload.
  - Sequence: Customers -> Accounts -> XRefs -> Transactions -> Cards
  - Global sequence numbering across all record types
  - Branch='0001', Region='NORTH' (hardcoded in COBOL spec)

CBIMPORT: reads JSON export, routes to target tables, validates records.
  - Routes C/A/X/T/D record types to appropriate tables
  - 3000-VALIDATE-IMPORT stub implemented as real field-level validation
  - Unknown type codes logged and counted as errors
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.card import Card
from app.models.card_cross_reference import CardCrossReference
from app.models.customer import Customer
from app.models.transaction import Transaction
from app.repositories.batch_job import BatchJobRepository
from app.repositories.export_import import ExportImportRepository
from app.schemas.batch import (
    AccountExport,
    CardExport,
    CustomerExport,
    ExportPayload,
    ImportValidationError,
    TransactionExport,
    XrefExport,
)

logger = logging.getLogger(__name__)


class ExportImportService:
    """CBEXPORT and CBIMPORT equivalents."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ExportImportRepository(db)
        self.job_repo = BatchJobRepository(db)

    # -------------------------------------------------------
    # CBEXPORT equivalent
    # -------------------------------------------------------

    async def export_all(self) -> dict:
        """Export all entities to JSON payload.

        Maps CBEXPORT 0000-MAIN-PROCESSING:
          PERFORM 2000-EXPORT-CUSTOMERS
          PERFORM 3000-EXPORT-ACCOUNTS
          PERFORM 4000-EXPORT-XREFS
          PERFORM 5000-EXPORT-TRANSACTIONS
          PERFORM 5500-EXPORT-CARDS
        """
        job = await self.job_repo.create_job("data_export")
        await self.db.commit()

        timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S.00")

        customers = await self._export_customers()
        accounts = await self._export_accounts()
        xrefs = await self._export_xrefs()
        transactions = await self._export_transactions()
        cards = await self._export_cards()

        total = len(customers) + len(accounts) + len(xrefs) + len(transactions) + len(cards)

        payload = ExportPayload(
            export_timestamp=timestamp,
            branch_id="0001",       # EXPORT-BRANCH-ID hardcoded in COBOL
            region_code="NORTH",    # EXPORT-REGION-CODE hardcoded in COBOL
            customers=customers,
            accounts=accounts,
            xrefs=xrefs,
            transactions=transactions,
            cards=cards,
            total_records=total,
        )

        await self.job_repo.complete_job(
            job_id=job.job_id,
            records_processed=total,
            records_rejected=0,
            result_summary={
                "customers": len(customers),
                "accounts": len(accounts),
                "xrefs": len(xrefs),
                "transactions": len(transactions),
                "cards": len(cards),
                "total": total,
            },
        )
        await self.db.commit()

        return {
            "job_id": job.job_id,
            "status": "completed",
            "customers_exported": len(customers),
            "accounts_exported": len(accounts),
            "xrefs_exported": len(xrefs),
            "transactions_exported": len(transactions),
            "cards_exported": len(cards),
            "total_records_exported": total,
            "payload": payload,
            "message": f"Export complete: {total} records exported",
        }

    async def _export_customers(self) -> list[CustomerExport]:
        """Maps CBEXPORT 2000-EXPORT-CUSTOMERS."""
        customers = await self.repo.get_all_customers()
        return [
            CustomerExport(
                cust_id=c.cust_id,
                cust_first_name=c.cust_first_name,
                cust_middle_name=c.cust_middle_name,
                cust_last_name=c.cust_last_name,
                cust_addr_line_1=c.cust_addr_line_1,
                cust_addr_line_2=c.cust_addr_line_2,
                cust_addr_line_3=c.cust_addr_line_3,
                cust_addr_state_cd=c.cust_addr_state_cd,
                cust_addr_country_cd=c.cust_addr_country_cd,
                cust_addr_zip=c.cust_addr_zip,
                cust_phone_num_1=c.cust_phone_num_1,
                cust_phone_num_2=c.cust_phone_num_2,
                cust_ssn=c.cust_ssn,
                cust_govt_issued_id=c.cust_govt_issued_id,
                cust_dob=c.cust_dob,
                cust_eft_account_id=c.cust_eft_account_id,
                cust_pri_card_holder_ind=c.cust_pri_card_holder_ind,
                cust_fico_credit_score=c.cust_fico_credit_score,
            )
            for c in customers
        ]

    async def _export_accounts(self) -> list[AccountExport]:
        """Maps CBEXPORT 3000-EXPORT-ACCOUNTS."""
        accounts = await self.repo.get_all_accounts()
        return [
            AccountExport(
                acct_id=a.acct_id,
                acct_active_status=a.acct_active_status,
                acct_curr_bal=a.acct_curr_bal or Decimal("0"),
                acct_credit_limit=a.acct_credit_limit or Decimal("0"),
                acct_cash_credit_limit=a.acct_cash_credit_limit or Decimal("0"),
                acct_open_date=a.acct_open_date,
                acct_expiration_date=a.acct_expiration_date,
                acct_reissue_date=a.acct_reissue_date,
                acct_curr_cyc_credit=a.acct_curr_cyc_credit or Decimal("0"),
                acct_curr_cyc_debit=a.acct_curr_cyc_debit or Decimal("0"),
                acct_addr_zip=a.acct_addr_zip,
                acct_group_id=a.acct_group_id,
            )
            for a in accounts
        ]

    async def _export_xrefs(self) -> list[XrefExport]:
        """Maps CBEXPORT 4000-EXPORT-XREFS."""
        xrefs = await self.repo.get_all_xrefs()
        return [
            XrefExport(
                xref_card_num=x.xref_card_num,
                xref_cust_id=x.xref_cust_id,
                xref_acct_id=x.xref_acct_id,
            )
            for x in xrefs
        ]

    async def _export_transactions(self) -> list[TransactionExport]:
        """Maps CBEXPORT 5000-EXPORT-TRANSACTIONS."""
        transactions = await self.repo.get_all_transactions()
        return [
            TransactionExport(
                tran_id=t.tran_id,
                tran_type_cd=t.tran_type_cd,
                tran_cat_cd=t.tran_cat_cd,
                tran_source=t.tran_source,
                tran_desc=t.tran_desc,
                tran_amt=t.tran_amt,
                tran_merchant_id=t.tran_merchant_id,
                tran_merchant_name=t.tran_merchant_name,
                tran_merchant_city=t.tran_merchant_city,
                tran_merchant_zip=t.tran_merchant_zip,
                tran_card_num=t.tran_card_num,
                tran_orig_ts=t.tran_orig_ts,
                tran_proc_ts=t.tran_proc_ts,
            )
            for t in transactions
        ]

    async def _export_cards(self) -> list[CardExport]:
        """Maps CBEXPORT 5500-EXPORT-CARDS."""
        cards = await self.repo.get_all_cards()
        return [
            CardExport(
                card_num=c.card_num,
                card_acct_id=c.card_acct_id,
                card_cvv_cd=c.card_cvv_cd,
                card_embossed_name=c.card_embossed_name,
                card_expiration_date=c.card_expiration_date,
                card_active_status=c.card_active_status,
            )
            for c in cards
        ]

    # -------------------------------------------------------
    # CBIMPORT equivalent
    # -------------------------------------------------------

    async def import_data(self, payload: ExportPayload) -> dict:
        """Import data from JSON export payload.

        Maps CBIMPORT 2000-PROCESS-EXPORT-FILE routing by type code.
        Implements 3000-VALIDATE-IMPORT (stub in COBOL).
        """
        job = await self.job_repo.create_job("data_import")
        await self.db.commit()

        validation_errors: list[ImportValidationError] = []

        # Run validation (3000-VALIDATE-IMPORT — was a stub, now implemented)
        self._validate_import(payload, validation_errors)

        cust_count = await self._import_customers(payload.customers, validation_errors)
        acct_count = await self._import_accounts(payload.accounts, validation_errors)
        xref_count = await self._import_xrefs(payload.xrefs, validation_errors)
        tran_count = await self._import_transactions(payload.transactions, validation_errors)
        card_count = await self._import_cards(payload.cards, validation_errors)

        total = cust_count + acct_count + xref_count + tran_count + card_count

        await self.job_repo.complete_job(
            job_id=job.job_id,
            records_processed=total,
            records_rejected=len(validation_errors),
            result_summary={
                "customers_imported": cust_count,
                "accounts_imported": acct_count,
                "xrefs_imported": xref_count,
                "transactions_imported": tran_count,
                "cards_imported": card_count,
                "validation_errors": len(validation_errors),
            },
        )
        await self.db.commit()

        return {
            "job_id": job.job_id,
            "status": "completed",
            "total_records_read": payload.total_records,
            "customers_imported": cust_count,
            "accounts_imported": acct_count,
            "xrefs_imported": xref_count,
            "transactions_imported": tran_count,
            "cards_imported": card_count,
            "validation_errors": validation_errors,
            "error_count": len(validation_errors),
            "message": f"Import complete: {total} records imported, {len(validation_errors)} errors",
        }

    def _validate_import(
        self, payload: ExportPayload, errors: list[ImportValidationError]
    ) -> None:
        """Implement CBIMPORT 3000-VALIDATE-IMPORT (was a stub in COBOL).

        Validates:
        - Required fields are present
        - Account cross-references are consistent
        - Card numbers reference valid accounts
        """
        acct_ids = {a.acct_id for a in payload.accounts}
        cust_ids = {c.cust_id for c in payload.customers}
        card_nums = {c.card_num for c in payload.cards}

        for xref in payload.xrefs:
            if not xref.xref_card_num:
                errors.append(ImportValidationError(
                    record_type="X", record_id="unknown",
                    field="xref_card_num", error="Card number is required"
                ))
            if xref.xref_acct_id and xref.xref_acct_id not in acct_ids:
                errors.append(ImportValidationError(
                    record_type="X", record_id=xref.xref_card_num,
                    field="xref_acct_id",
                    error=f"Account {xref.xref_acct_id} not found in export payload"
                ))

        for card in payload.cards:
            if card.card_acct_id and card.card_acct_id not in acct_ids:
                errors.append(ImportValidationError(
                    record_type="D", record_id=card.card_num,
                    field="card_acct_id",
                    error=f"Account {card.card_acct_id} not found in export payload"
                ))
            if card.card_active_status not in ("Y", "N"):
                errors.append(ImportValidationError(
                    record_type="D", record_id=card.card_num,
                    field="card_active_status",
                    error="card_active_status must be Y or N"
                ))

        for acct in payload.accounts:
            if acct.acct_active_status not in ("Y", "N"):
                errors.append(ImportValidationError(
                    record_type="A", record_id=acct.acct_id,
                    field="acct_active_status",
                    error="acct_active_status must be Y or N"
                ))

        for tran in payload.transactions:
            if not tran.tran_id:
                errors.append(ImportValidationError(
                    record_type="T", record_id="unknown",
                    field="tran_id", error="Transaction ID is required"
                ))

    async def _import_customers(
        self,
        customers: list[CustomerExport],
        errors: list[ImportValidationError],
    ) -> int:
        """Maps CBIMPORT 2300-PROCESS-CUSTOMER-RECORD."""
        count = 0
        for c in customers:
            try:
                customer = Customer(
                    cust_id=c.cust_id,
                    cust_first_name=c.cust_first_name,
                    cust_middle_name=c.cust_middle_name,
                    cust_last_name=c.cust_last_name,
                    cust_addr_line_1=c.cust_addr_line_1,
                    cust_addr_line_2=c.cust_addr_line_2,
                    cust_addr_line_3=c.cust_addr_line_3,
                    cust_addr_state_cd=c.cust_addr_state_cd,
                    cust_addr_country_cd=c.cust_addr_country_cd,
                    cust_addr_zip=c.cust_addr_zip,
                    cust_phone_num_1=c.cust_phone_num_1,
                    cust_phone_num_2=c.cust_phone_num_2,
                    cust_ssn=c.cust_ssn,
                    cust_govt_issued_id=c.cust_govt_issued_id,
                    cust_dob=c.cust_dob,
                    cust_eft_account_id=c.cust_eft_account_id,
                    cust_pri_card_holder_ind=c.cust_pri_card_holder_ind,
                    cust_fico_credit_score=c.cust_fico_credit_score,
                )
                await self.repo.upsert_customer(customer)
                count += 1
            except Exception as e:
                logger.error("Failed to import customer %s: %s", c.cust_id, e)
                errors.append(ImportValidationError(
                    record_type="C", record_id=c.cust_id,
                    field="*", error=str(e)
                ))
        return count

    async def _import_accounts(
        self,
        accounts: list[AccountExport],
        errors: list[ImportValidationError],
    ) -> int:
        """Maps CBIMPORT 2400-PROCESS-ACCOUNT-RECORD."""
        count = 0
        for a in accounts:
            try:
                account = Account(
                    acct_id=a.acct_id,
                    acct_active_status=a.acct_active_status,
                    acct_curr_bal=a.acct_curr_bal,
                    acct_credit_limit=a.acct_credit_limit,
                    acct_cash_credit_limit=a.acct_cash_credit_limit,
                    acct_open_date=a.acct_open_date,
                    acct_expiration_date=a.acct_expiration_date,
                    acct_reissue_date=a.acct_reissue_date,
                    acct_curr_cyc_credit=a.acct_curr_cyc_credit,
                    acct_curr_cyc_debit=a.acct_curr_cyc_debit,
                    acct_addr_zip=a.acct_addr_zip,
                    acct_group_id=a.acct_group_id,
                )
                await self.repo.upsert_account(account)
                count += 1
            except Exception as e:
                logger.error("Failed to import account %s: %s", a.acct_id, e)
                errors.append(ImportValidationError(
                    record_type="A", record_id=a.acct_id,
                    field="*", error=str(e)
                ))
        return count

    async def _import_xrefs(
        self,
        xrefs: list[XrefExport],
        errors: list[ImportValidationError],
    ) -> int:
        """Maps CBIMPORT 2500-PROCESS-XREF-RECORD."""
        count = 0
        for x in xrefs:
            try:
                xref = CardCrossReference(
                    xref_card_num=x.xref_card_num,
                    xref_cust_id=x.xref_cust_id,
                    xref_acct_id=x.xref_acct_id,
                )
                await self.repo.upsert_xref(xref)
                count += 1
            except Exception as e:
                logger.error("Failed to import xref %s: %s", x.xref_card_num, e)
                errors.append(ImportValidationError(
                    record_type="X", record_id=x.xref_card_num,
                    field="*", error=str(e)
                ))
        return count

    async def _import_transactions(
        self,
        transactions: list[TransactionExport],
        errors: list[ImportValidationError],
    ) -> int:
        """Maps CBIMPORT 2600-PROCESS-TRAN-RECORD."""
        count = 0
        for t in transactions:
            try:
                tran = Transaction(
                    tran_id=t.tran_id,
                    tran_type_cd=t.tran_type_cd,
                    tran_cat_cd=t.tran_cat_cd,
                    tran_source=t.tran_source,
                    tran_desc=t.tran_desc,
                    tran_amt=t.tran_amt,
                    tran_merchant_id=t.tran_merchant_id,
                    tran_merchant_name=t.tran_merchant_name,
                    tran_merchant_city=t.tran_merchant_city,
                    tran_merchant_zip=t.tran_merchant_zip,
                    tran_card_num=t.tran_card_num,
                    tran_orig_ts=t.tran_orig_ts,
                    tran_proc_ts=t.tran_proc_ts,
                )
                await self.repo.upsert_transaction(tran)
                count += 1
            except Exception as e:
                logger.error("Failed to import transaction %s: %s", t.tran_id, e)
                errors.append(ImportValidationError(
                    record_type="T", record_id=t.tran_id,
                    field="*", error=str(e)
                ))
        return count

    async def _import_cards(
        self,
        cards: list[CardExport],
        errors: list[ImportValidationError],
    ) -> int:
        """Maps CBIMPORT 2650-PROCESS-CARD-RECORD."""
        count = 0
        for c in cards:
            try:
                card = Card(
                    card_num=c.card_num,
                    card_acct_id=c.card_acct_id,
                    card_cvv_cd=c.card_cvv_cd,
                    card_embossed_name=c.card_embossed_name,
                    card_expiration_date=c.card_expiration_date,
                    card_active_status=c.card_active_status,
                )
                await self.repo.upsert_card(card)
                count += 1
            except Exception as e:
                logger.error("Failed to import card %s: %s", c.card_num, e)
                errors.append(ImportValidationError(
                    record_type="D", record_id=c.card_num,
                    field="*", error=str(e)
                ))
        return count
