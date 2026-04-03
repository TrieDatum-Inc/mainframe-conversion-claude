"""Custom exception classes for the Account Management module.

These map to COBOL error conditions and 88-level flags from the spec:
  AccountNotFoundError    → DID-NOT-FIND-ACCT-IN-ACCTDAT / DID-NOT-FIND-ACCT-IN-CARDXREF
  CustomerNotFoundError   → DID-NOT-FIND-CUST-IN-CUSTDAT
  ConcurrentModificationError → DATA-WAS-CHANGED-BEFORE-UPDATE
  LockAcquisitionError    → COULD-NOT-LOCK-ACCT-FOR-UPDATE / COULD-NOT-LOCK-CUST-FOR-UPDATE
"""


class AccountManagementError(Exception):
    """Base exception for all account management errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class AccountNotFoundError(AccountManagementError):
    """Account not found in account master file or cross-reference.

    Maps to COBOL conditions:
      DID-NOT-FIND-ACCT-IN-ACCTDAT
      DID-NOT-FIND-ACCT-IN-CARDXREF
    """


class CustomerNotFoundError(AccountManagementError):
    """Customer not found in customer master file.

    Maps to COBOL condition: DID-NOT-FIND-CUST-IN-CUSTDAT
    """


class ConcurrentModificationError(AccountManagementError):
    """Record was modified by another user since it was fetched.

    Maps to COBOL condition: DATA-WAS-CHANGED-BEFORE-UPDATE
    (implemented via 9700-CHECK-CHANGE-IN-REC comparison).
    """


class LockAcquisitionError(AccountManagementError):
    """Could not acquire exclusive lock for update.

    Maps to COBOL conditions:
      COULD-NOT-LOCK-ACCT-FOR-UPDATE
      COULD-NOT-LOCK-CUST-FOR-UPDATE
    """
