class CardNotFoundError(Exception):
    def __init__(self, card_num: str) -> None:
        self.card_num = card_num
        super().__init__(f"Did not find cards for this search condition: {card_num}")


class ConcurrentModificationError(Exception):
    def __init__(self, card_num: str, refreshed_card: object | None = None) -> None:
        self.card_num = card_num
        self.refreshed_card = refreshed_card
        super().__init__(f"Record was changed by another user since last read: {card_num}")


class CardUpdateLockError(Exception):
    def __init__(self, card_num: str) -> None:
        self.card_num = card_num
        super().__init__(f"Changes unsuccessful. Please try again: {card_num}")


class ValidationError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
