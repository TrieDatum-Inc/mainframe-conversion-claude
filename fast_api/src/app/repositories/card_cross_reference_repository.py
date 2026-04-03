"""CardCrossReference repository — data access for CXACAIX AIX file equivalent.

Maps CICS file commands from COBIL00C to async SQLAlchemy queries.
"""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card_cross_reference import CardCrossReference

logger = logging.getLogger(__name__)


class CardCrossReferenceRepository:
    """Data access for the card_cross_references table.

    CICS equivalent:
      READ-CXACAIX-FILE → get_by_acct_id()

    COBIL00C pattern (line 408):
      EXEC CICS READ DATASET('CXACAIX') INTO(CARD-XREF-RECORD) RIDFLD(XREF-ACCT-ID)
      Reads the alternate index on acct_id to retrieve the card number.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_acct_id(self, acct_id: str) -> CardCrossReference | None:
        """Find the card cross-reference record for a given account ID.

        Maps: EXEC CICS READ DATASET('CXACAIX') RIDFLD(XREF-ACCT-ID)
        In the COBOL alternate index, acct_id is the AIX key.
        Here we use an indexed column query.
        Returns the first card linked to the account.
        """
        result = await self._session.execute(
            select(CardCrossReference)
            .where(CardCrossReference.acct_id == int(acct_id))
            .limit(1)
        )
        return result.scalar_one_or_none()
