"""
Transaction repository — data access layer.

Replaces VSAM KSDS EXEC CICS operations on TRANSACT file (CVTRA05Y).
Also handles TranCatBal (CVTRA01Y), DisclosureGroup (CVTRA02Y),
TransactionType (DB2), and TransactionCategory (DB2).

COTRN00C uses STARTBR/READNEXT/READPREV for paginated browsing (10 rows/page).
COTRN02C uses READPREV to find the last tran_id for auto-increment.
COBIL00C uses STARTBR/READPREV to browse recent transactions + WRITE for payment.
"""

from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateKeyError, ResourceNotFoundError
from app.infrastructure.orm.transaction_orm import (
    DisclosureGroupORM,
    TranCatBalORM,
    TransactionCategoryORM,
    TransactionORM,
    TransactionTypeORM,
)


class TransactionRepository:
    """
    Transaction VSAM KSDS (TRANSACT file) operations.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, tran_id: str) -> TransactionORM:
        """
        Read transaction by primary key.
        Equivalent to: EXEC CICS READ DATASET('TRANSACT') RIDFLD(tran_id)
        """
        stmt = select(TransactionORM).where(TransactionORM.tran_id == tran_id)
        result = await self.db.execute(stmt)
        txn = result.scalar_one_or_none()
        if txn is None:
            raise ResourceNotFoundError("Transaction", tran_id)
        return txn

    async def get_by_id_or_none(self, tran_id: str) -> Optional[TransactionORM]:
        """Read transaction; return None if not found."""
        stmt = select(TransactionORM).where(TransactionORM.tran_id == tran_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_last_tran_id(self) -> Optional[str]:
        """
        Get the last transaction ID for new ID generation.
        COTRN02C: EXEC CICS STARTBR + READPREV -> get last record -> new_id = last_id + 1
        """
        stmt = (
            select(TransactionORM.tran_id)
            .order_by(desc(TransactionORM.tran_id))
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_paginated_forward(
        self,
        page_size: int,
        start_tran_id: Optional[str] = None,
        card_num_filter: Optional[str] = None,
    ) -> Tuple[List[TransactionORM], bool]:
        """
        Forward-paginated transaction list.
        Equivalent to COTRN00C 9000-STARTBR-TRANSACT-FILE + READNEXT.
        """
        conditions = []
        if start_tran_id:
            conditions.append(TransactionORM.tran_id >= start_tran_id)
        if card_num_filter:
            conditions.append(TransactionORM.card_num == card_num_filter)

        from sqlalchemy import and_
        stmt = (
            select(TransactionORM)
            .where(and_(*conditions) if conditions else True)
            .order_by(asc(TransactionORM.tran_id))
            .limit(page_size + 1)
        )
        result = await self.db.execute(stmt)
        rows = list(result.scalars().all())
        has_next = len(rows) > page_size
        return rows[:page_size], has_next

    async def list_paginated_backward(
        self,
        page_size: int,
        end_tran_id: str,
        card_num_filter: Optional[str] = None,
    ) -> Tuple[List[TransactionORM], bool]:
        """
        Backward-paginated transaction list.
        Equivalent to COTRN00C READPREV.
        """
        conditions = [TransactionORM.tran_id <= end_tran_id]
        if card_num_filter:
            conditions.append(TransactionORM.card_num == card_num_filter)

        from sqlalchemy import and_
        stmt = (
            select(TransactionORM)
            .where(and_(*conditions))
            .order_by(desc(TransactionORM.tran_id))
            .limit(page_size + 1)
        )
        result = await self.db.execute(stmt)
        rows = list(result.scalars().all())
        has_prev = len(rows) > page_size
        return list(reversed(rows[:page_size])), has_prev

    async def create(self, transaction: TransactionORM) -> TransactionORM:
        """
        Write new transaction.
        Equivalent to: EXEC CICS WRITE DATASET('TRANSACT')
        Used by COTRN02C (add transaction) and COBIL00C (payment transaction).
        """
        existing = await self.get_by_id_or_none(transaction.tran_id)
        if existing is not None:
            raise DuplicateKeyError("Transaction", transaction.tran_id)
        self.db.add(transaction)
        await self.db.flush()
        return transaction

    async def get_by_card_num_recent(
        self,
        card_num: str,
        limit: int = 10,
    ) -> List[TransactionORM]:
        """
        Browse recent transactions by card number.
        Equivalent to COBIL00C: STARTBR + READPREV on TRANSACT keyed by card_num.
        """
        stmt = (
            select(TransactionORM)
            .where(TransactionORM.card_num == card_num)
            .order_by(desc(TransactionORM.orig_ts))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_balance_for_account(self, acct_id: int) -> Decimal:
        """
        Compute total transaction amount for an account's cards.
        Used in report generation (CBTRN03C equivalent).
        """
        from sqlalchemy import join
        from app.infrastructure.orm.card_orm import CardORM
        stmt = (
            select(func.sum(TransactionORM.tran_amt))
            .join(CardORM, TransactionORM.card_num == CardORM.card_num)
            .where(CardORM.acct_id == acct_id)
        )
        result = await self.db.execute(stmt)
        total = result.scalar_one_or_none()
        return total if total is not None else Decimal("0.00")


class TranCatBalRepository:
    """
    Transaction Category Balance VSAM KSDS operations (CVTRA01Y).
    Used by CBACT04C (interest calc) and CBTRN02C (category balance update).
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(
        self,
        acct_id: int,
        tran_type_cd: str,
        tran_cat_cd: int,
    ) -> Optional[TranCatBalORM]:
        """Read category balance by composite key."""
        stmt = select(TranCatBalORM).where(
            TranCatBalORM.acct_id == acct_id,
            TranCatBalORM.tran_type_cd == tran_type_cd,
            TranCatBalORM.tran_cat_cd == tran_cat_cd,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_for_account(self, acct_id: int) -> List[TranCatBalORM]:
        """Read all category balances for an account (CBACT04C sequential read)."""
        stmt = (
            select(TranCatBalORM)
            .where(TranCatBalORM.acct_id == acct_id)
            .order_by(TranCatBalORM.tran_type_cd, TranCatBalORM.tran_cat_cd)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def upsert(
        self,
        acct_id: int,
        tran_type_cd: str,
        tran_cat_cd: int,
        amount: Decimal,
    ) -> TranCatBalORM:
        """
        Insert or update category balance.
        CBTRN02C: REWRITE or WRITE based on whether record exists.
        """
        existing = await self.get(acct_id, tran_type_cd, tran_cat_cd)
        if existing is not None:
            existing.tran_cat_bal += amount
            await self.db.flush()
            return existing
        new_rec = TranCatBalORM(
            acct_id=acct_id,
            tran_type_cd=tran_type_cd,
            tran_cat_cd=tran_cat_cd,
            tran_cat_bal=amount,
        )
        self.db.add(new_rec)
        await self.db.flush()
        return new_rec

    async def get_all_sequential(self) -> List[TranCatBalORM]:
        """
        Sequential read of all TranCatBal records.
        CBACT04C: reads TCATBAL-FILE sequentially as primary driver.
        """
        stmt = select(TranCatBalORM).order_by(
            TranCatBalORM.acct_id,
            TranCatBalORM.tran_type_cd,
            TranCatBalORM.tran_cat_cd,
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class DisclosureGroupRepository:
    """
    Disclosure Group interest rate lookup (CVTRA02Y).
    Used by CBACT04C for interest rate lookup by account group + type + category.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(
        self,
        acct_group_id: str,
        tran_type_cd: str,
        tran_cat_cd: int,
    ) -> Optional[DisclosureGroupORM]:
        """
        Lookup interest rate by composite key.
        CBACT04C: EXEC READ DATASET('DISCGRP') RIDFLD(composite-key)
        """
        stmt = select(DisclosureGroupORM).where(
            DisclosureGroupORM.acct_group_id == acct_group_id,
            DisclosureGroupORM.tran_type_cd == tran_type_cd,
            DisclosureGroupORM.tran_cat_cd == tran_cat_cd,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


class TransactionTypeRepository:
    """
    Transaction Type DB2 table operations.
    Replaces DB2 cursor-based SELECT in COTRTLIC/COTRTUPC.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_code(self, tran_type_cd: str) -> TransactionTypeORM:
        """Read transaction type by code (DB2 SELECT WHERE type_cd = ?)."""
        stmt = select(TransactionTypeORM).where(
            TransactionTypeORM.tran_type_cd == tran_type_cd.upper()
        )
        result = await self.db.execute(stmt)
        ttype = result.scalar_one_or_none()
        if ttype is None:
            raise ResourceNotFoundError("TransactionType", tran_type_cd)
        return ttype

    async def get_by_code_or_none(self, tran_type_cd: str) -> Optional[TransactionTypeORM]:
        """Read transaction type; return None if not found."""
        stmt = select(TransactionTypeORM).where(
            TransactionTypeORM.tran_type_cd == tran_type_cd.upper()
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_paginated(
        self,
        page_size: int,
        start_type_cd: Optional[str] = None,
        type_cd_filter: Optional[str] = None,
        desc_filter: Optional[str] = None,
    ) -> Tuple[List[TransactionTypeORM], bool]:
        """
        Cursor-based forward pagination.
        Equivalent to COTRTLIC DB2 cursor C-TR-TYPE-FORWARD:
          SELECT type_cd, type_desc FROM TRANSACTION_TYPE
          WHERE type_cd >= :start_cd
          ORDER BY type_cd
          FETCH FIRST :page_size+1 ROWS ONLY
        """
        from sqlalchemy import and_
        conditions = []
        if start_type_cd:
            conditions.append(TransactionTypeORM.tran_type_cd >= start_type_cd.upper())
        if type_cd_filter:
            conditions.append(
                TransactionTypeORM.tran_type_cd.ilike(f"%{type_cd_filter}%")
            )
        if desc_filter:
            conditions.append(
                TransactionTypeORM.tran_type_desc.ilike(f"%{desc_filter}%")
            )

        stmt = (
            select(TransactionTypeORM)
            .where(and_(*conditions) if conditions else True)
            .order_by(asc(TransactionTypeORM.tran_type_cd))
            .limit(page_size + 1)
        )
        result = await self.db.execute(stmt)
        rows = list(result.scalars().all())
        has_next = len(rows) > page_size
        return rows[:page_size], has_next

    async def create(self, ttype: TransactionTypeORM) -> TransactionTypeORM:
        """
        INSERT new transaction type.
        COTRTUPC: EXEC SQL INSERT INTO CARDDEMO.TRANSACTION_TYPE
        """
        existing = await self.get_by_code_or_none(ttype.tran_type_cd)
        if existing is not None:
            raise DuplicateKeyError("TransactionType", ttype.tran_type_cd)
        self.db.add(ttype)
        await self.db.flush()
        return ttype

    async def update(self, ttype: TransactionTypeORM) -> TransactionTypeORM:
        """UPDATE transaction type description. COTRTUPC: EXEC SQL UPDATE."""
        await self.db.flush()
        return ttype

    async def delete(self, tran_type_cd: str) -> None:
        """
        DELETE transaction type.
        COTRTLIC: EXEC SQL DELETE FROM CARDDEMO.TRANSACTION_TYPE WHERE type_cd = ?
        """
        ttype = await self.get_by_code(tran_type_cd)
        await self.db.delete(ttype)
        await self.db.flush()
