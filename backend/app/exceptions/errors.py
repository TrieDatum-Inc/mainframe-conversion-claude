"""
Custom exception classes for the CardDemo API.
"""

from fastapi import HTTPException, status


class CardDemoException(Exception):
    """Base exception for all CardDemo application errors."""

    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class AuthenticationError(CardDemoException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, error_code="AUTHENTICATION_ERROR")


class InvalidTokenError(CardDemoException):
    """Raised when a JWT token is invalid or expired."""

    def __init__(self, message: str = "Could not validate credentials"):
        super().__init__(message=message, error_code="INVALID_TOKEN")
