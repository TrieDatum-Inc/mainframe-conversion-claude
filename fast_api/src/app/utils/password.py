"""Password hashing utilities.

COBOL stored passwords as PIC X(08) plaintext in USRSEC VSAM.
We replace that with bcrypt hashing.  The plaintext is never stored or
returned by any API endpoint.
"""
import bcrypt

from app.config import get_settings


def hash_password(plaintext: str) -> str:
    """Hash a plaintext password using bcrypt.

    Args:
        plaintext: The raw password (up to 72 bytes processed by bcrypt).

    Returns:
        bcrypt hash string suitable for storage in users.password.
    """
    settings = get_settings()
    salt = bcrypt.gensalt(rounds=settings.bcrypt_rounds)
    return bcrypt.hashpw(plaintext.encode("utf-8"), salt).decode("utf-8")


def verify_password(plaintext: str, hashed: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash.

    Args:
        plaintext: The raw password attempt.
        hashed: The stored bcrypt hash.

    Returns:
        True if the password matches, False otherwise.
    """
    return bcrypt.checkpw(plaintext.encode("utf-8"), hashed.encode("utf-8"))
