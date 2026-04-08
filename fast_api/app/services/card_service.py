"""
Card service — business logic from COCRDLIC, COCRDSLC, COCRDUPC.

Paragraph mapping:
  COCRDLIC BROWSE-CARDS-FORWARD     → list_cards() with direction='forward'
  COCRDLIC BROWSE-CARDS-BACKWARD    → list_cards() with direction='backward'
  COCRDSLC READ-CARD-DATA           → get_card()
  COCRDUPC PROCESS-ENTER-KEY        → update_card()
  COCRDUPC VALIDATE-INPUT-FIELDS    → _validate_card_update()

Business rules:
  1. Browse uses CARDAIX (alt-index on CARD-ACCT-ID) — keyset on card_num
  2. CARD-ACTIVE-STATUS must be 'Y' or 'N'
  3. Read-then-rewrite pattern for updates
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import Card
from app.repositories.card_repo import CardRepository
from app.schemas.card import CardListResponse, CardResponse, CardUpdateRequest
from app.utils.error_handlers import ValidationError


class CardService:
    """Card business logic from COCRDLIC, COCRDSLC, COCRDUPC."""

    def __init__(self, db: AsyncSession) -> None:
        self._repo = CardRepository(db)

    async def list_cards(
        self,
        account_id: int | None = None,
        cursor: str | None = None,
        limit: int = 10,
        direction: str = "forward",
    ) -> CardListResponse:
        """
        COCRDLIC BROWSE-CARDS paragraph.

        Browses CARDAIX (alternate index on CARD-ACCT-ID) using STARTBR/READNEXT.
        Supports bidirectional paging (READNEXT / READPREV).

        STARTBR with GTEQ → WHERE card_num >= :cursor
        Each page tracks CDEMO-CL00-CARDNUM-FIRST and CDEMO-CL00-CARDNUM-LAST.

        Args:
            account_id: Filter by CARD-ACCT-ID (browse CARDAIX).
            cursor: Keyset cursor (card_num from previous page).
            limit: Page size.
            direction: 'forward' (READNEXT) or 'backward' (READPREV).

        Returns:
            CardListResponse with pagination cursors.
        """
        if account_id is not None:
            cards, total, has_more = await self._repo.list_by_account(
                acct_id=account_id,
                cursor=cursor,
                limit=limit,
                direction=direction,
            )
        else:
            cards, total, has_more = await self._repo.list_all_paginated(
                cursor=cursor, limit=limit, direction=direction
            )

        items = [self._build_response(c) for c in cards]
        first = cards[0].card_num.strip() if cards else None
        last = cards[-1].card_num.strip() if cards else None

        if direction == "backward":
            has_prev = has_more
            has_next = cursor is not None
        else:
            has_next = has_more
            has_prev = cursor is not None

        return CardListResponse(
            items=items,
            total=total,
            next_cursor=last if has_next and cards else None,
            prev_cursor=first if has_prev and cards else None,
        )

    async def get_card(self, card_num: str) -> CardResponse:
        """
        COCRDSLC READ-CARD-DATA: EXEC CICS READ FILE('CARDDAT') RIDFLD(CARD-NUM).

        Returns card details. Raises RecordNotFoundError if not found.
        """
        card = await self._repo.get_by_card_num(card_num)
        return self._build_response(card)

    async def update_card(self, card_num: str, request: CardUpdateRequest) -> CardResponse:
        """
        COCRDUPC PROCESS-ENTER-KEY → validate → EXEC CICS REWRITE FILE('CARDDAT').

        Read-then-rewrite pattern (COCRDUPC reads card first, modifies fields,
        then uses EXEC CICS REWRITE).

        Business rules:
          - CARD-ACTIVE-STATUS must be 'Y' or 'N'
          - Only embossed_name and active_status are updatable via COCRDUPC
        """
        # COCRDUPC: EXEC CICS READ FILE('CARDDAT') before REWRITE
        card = await self._repo.get_by_card_num(card_num)

        self._apply_card_changes(card, request)

        updated = await self._repo.update(card)
        return self._build_response(updated)

    def _apply_card_changes(self, card: Card, request: CardUpdateRequest) -> None:
        """
        COCRDUPC: apply only provided field changes.
        Mirrors COBOL MOVE — only explicitly provided fields are updated.
        """
        if request.embossed_name is not None:
            card.embossed_name = request.embossed_name
        if request.active_status is not None:
            card.active_status = request.active_status

    @staticmethod
    def _build_response(card: Card) -> CardResponse:
        """Build CardResponse from ORM model."""
        return CardResponse(
            card_num=card.card_num.strip(),
            acct_id=card.acct_id,
            cvv_cd=card.cvv_cd,
            embossed_name=card.embossed_name,
            expiration_date=card.expiration_date,
            active_status=card.active_status,
        )
