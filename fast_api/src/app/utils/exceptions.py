"""Custom exception classes for the CardDemo Transaction Processing module."""


class CardDemoBaseError(Exception):
    """Base exception for all CardDemo application errors."""


class TransactionNotFoundError(CardDemoBaseError):
    """Transaction ID not found in TRANSACT file. Mirrors DFHRESP(NOTFND) on READ."""


class DuplicateTransactionError(CardDemoBaseError):
    """Transaction ID already exists. Mirrors DFHRESP(DUPKEY) / DFHRESP(DUPREC) on WRITE."""


class CardNotFoundError(CardDemoBaseError):
    """Card number not found in CCXREF. Mirrors DFHRESP(NOTFND) on READ-CCXREF-FILE."""


class AccountNotFoundError(CardDemoBaseError):
    """Account ID not found in CXACAIX. Mirrors DFHRESP(NOTFND) on READ-CXACAIX-FILE."""


class AccountInactiveError(CardDemoBaseError):
    """Account is not active (acct_active_status != 'Y')."""


class ValidationError(CardDemoBaseError):
    """General input validation failure."""
