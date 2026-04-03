"""Disclosure group data access repository.

Maps CBACT04C 1200-GET-INTEREST-RATE and 1200-A-GET-DEFAULT-INT-RATE.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.disclosure_group import DisclosureGroup

DEFAULT_GROUP_ID = "DEFAULT"


class DisclosureGroupRepository:
    """Data access for disclosure_groups table (DISCGRP KSDS / CVTRA02Y)."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_rate(
        self,
        group_id: str,
        tran_type_cd: str,
        tran_cat_cd: str,
    ) -> DisclosureGroup | None:
        """Random READ by composite key (group_id + type + category).

        Maps CBACT04C 1200-GET-INTEREST-RATE:
          READ DISCGRP-FILE by FD-DISCGRP-KEY (group + type + category).
        """
        result = await self.db.execute(
            select(DisclosureGroup).where(
                DisclosureGroup.group_id == group_id,
                DisclosureGroup.tran_type_cd == tran_type_cd,
                DisclosureGroup.tran_cat_cd == tran_cat_cd,
            )
        )
        return result.scalar_one_or_none()

    async def get_rate_with_default_fallback(
        self,
        group_id: str,
        tran_type_cd: str,
        tran_cat_cd: str,
    ) -> DisclosureGroup | None:
        """Look up rate; fall back to DEFAULT group if specific group not found.

        Maps CBACT04C 1200-GET-INTEREST-RATE + 1200-A-GET-DEFAULT-INT-RATE:
          IF status = '23' (not found) -> retry with FD-DIS-ACCT-GROUP-ID = 'DEFAULT'
        """
        rate = await self.get_rate(group_id, tran_type_cd, tran_cat_cd)
        if rate is None and group_id != DEFAULT_GROUP_ID:
            rate = await self.get_rate(DEFAULT_GROUP_ID, tran_type_cd, tran_cat_cd)
        return rate
