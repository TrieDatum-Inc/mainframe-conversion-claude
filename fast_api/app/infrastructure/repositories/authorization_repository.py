"""
Authorization repository — data access layer.

Replaces IMS DL/I operations from:
  COPAUS0C: GN (get next) on PAUTSUM0 segments (summary list)
  COPAUS1C: GHU (get hold unique) on PAUTDTL1 segment (detail view)
  COPAUA0C: ISRT/REPL on both summary and detail segments
  COPAUS2C: DB2 INSERT/UPDATE on AUTHFRDS table

IMS operations mapped:
  GU/GHU  -> SELECT by primary key
  GN/GHN  -> paginated SELECT with cursor
  ISRT    -> INSERT
  REPL    -> UPDATE (after GHU)
"""

from datetime import date, datetime, time
from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError
from app.infrastructure.orm.authorization_orm import (
    AuthDetailORM,
    AuthFraudORM,
    AuthSummaryORM,
)


class AuthSummaryRepository:
    """IMS PAUTSUM0 segment (CIPAUSMY) operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_acct_id(self, acct_id: int) -> AuthSummaryORM:
        """
        IMS GHU (Get Hold Unique) on PAUTSUM0 by account ID.
        COPAUS0C: reads summary segments for display.
        """
        stmt = select(AuthSummaryORM).where(AuthSummaryORM.acct_id == acct_id)
        result = await self.db.execute(stmt)
        summary = result.scalar_one_or_none()
        if summary is None:
            raise ResourceNotFoundError("AuthSummary", str(acct_id))
        return summary

    async def get_by_acct_id_or_none(self, acct_id: int) -> Optional[AuthSummaryORM]:
        """Read summary; return None if not found."""
        stmt = select(AuthSummaryORM).where(AuthSummaryORM.acct_id == acct_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(
        self,
        account_id_filter: Optional[int] = None,
    ) -> List[AuthSummaryORM]:
        """
        Sequential read of authorization summaries.
        COPAUS0C: displays list of accounts with pending authorizations.
        """
        if account_id_filter is not None:
            stmt = select(AuthSummaryORM).where(
                AuthSummaryORM.acct_id == account_id_filter
            )
        else:
            stmt = select(AuthSummaryORM).order_by(AuthSummaryORM.acct_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def upsert(self, summary: AuthSummaryORM) -> AuthSummaryORM:
        """
        Insert or update summary (IMS ISRT or REPL).
        COPAUA0C: creates summary if not exists, updates running totals.
        """
        existing = await self.get_by_acct_id_or_none(summary.acct_id)
        if existing is not None:
            # Update running totals (IMS REPL)
            existing.curr_bal = summary.curr_bal
            existing.approved_count = summary.approved_count
            existing.approved_amt = summary.approved_amt
            existing.declined_count = summary.declined_count
            existing.declined_amt = summary.declined_amt
            existing.auth_status = summary.auth_status
            await self.db.flush()
            return existing
        self.db.add(summary)
        await self.db.flush()
        return summary


class AuthDetailRepository:
    """IMS PAUTDTL1 segment (CIPAUDTY) operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_key(
        self,
        auth_date: date,
        auth_time: time,
        acct_id: int,
    ) -> AuthDetailORM:
        """
        IMS GHU on PAUTDTL1 by composite key (date + time + acct_id).
        COPAUS1C: reads detail for display + potential fraud flag.
        """
        stmt = select(AuthDetailORM).where(
            and_(
                AuthDetailORM.auth_date == auth_date,
                AuthDetailORM.auth_time == auth_time,
                AuthDetailORM.acct_id == acct_id,
            )
        )
        result = await self.db.execute(stmt)
        detail = result.scalar_one_or_none()
        if detail is None:
            raise ResourceNotFoundError(
                "AuthDetail",
                f"{auth_date}T{auth_time}@{acct_id}",
            )
        return detail

    async def get_for_account(self, acct_id: int) -> List[AuthDetailORM]:
        """
        Get all detail records for an account (IMS GNP - get next parent).
        COPAUS1C: lists auth details under a selected summary.
        """
        stmt = (
            select(AuthDetailORM)
            .where(AuthDetailORM.acct_id == acct_id)
            .order_by(AuthDetailORM.auth_date, AuthDetailORM.auth_time)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, detail: AuthDetailORM) -> AuthDetailORM:
        """IMS ISRT on PAUTDTL1 (COPAUA0C: write new authorization detail)."""
        self.db.add(detail)
        await self.db.flush()
        return detail

    async def update_fraud_flag(
        self,
        auth_date: date,
        auth_time: time,
        acct_id: int,
        fraud_flag: str,
    ) -> AuthDetailORM:
        """
        Update fraud flag on detail record (IMS REPL after GHU).
        COPAUS1C: LINK to COPAUS2C which sets fraud_flag='Y'.
        """
        detail = await self.get_by_key(auth_date, auth_time, acct_id)
        detail.fraud_flag = fraud_flag
        await self.db.flush()
        return detail


class AuthFraudRepository:
    """DB2 CARDDEMO.AUTHFRDS table operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_card_and_date(
        self,
        card_num: str,
        auth_date: date,
        auth_time: time,
    ) -> Optional[AuthFraudORM]:
        """
        SELECT fraud record by card + date + time.
        COPAUS2C checks for existing record to decide INSERT vs UPDATE.
        """
        stmt = select(AuthFraudORM).where(
            and_(
                AuthFraudORM.card_num == card_num,
                AuthFraudORM.auth_date == auth_date,
                AuthFraudORM.auth_time == auth_time,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, fraud: AuthFraudORM) -> AuthFraudORM:
        """
        INSERT new fraud record.
        COPAUS2C: EXEC SQL INSERT INTO CARDDEMO.AUTHFRDS ...
        """
        fraud.flagged_ts = datetime.utcnow()
        self.db.add(fraud)
        await self.db.flush()
        return fraud

    async def update(self, fraud: AuthFraudORM) -> AuthFraudORM:
        """
        UPDATE existing fraud record.
        COPAUS2C: EXEC SQL UPDATE CARDDEMO.AUTHFRDS SET ...
        """
        fraud.flagged_ts = datetime.utcnow()
        await self.db.flush()
        return fraud
