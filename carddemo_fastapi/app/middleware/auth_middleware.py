"""JWT Bearer authentication middleware.

Replaces the CICS RETURN TRANSID pattern for maintaining user session.
In COBOL, the COMMAREA carried user context between pseudo-conversational
transactions. Here, a JWT Bearer token carries the same context.
"""

from fastapi import Request, HTTPException, status
from jose import JWTError, jwt

from app.config import settings


async def verify_token(request: Request):
    """Middleware-level token verification (optional use).

    For most routes, the Depends(get_current_user) dependency
    handles authentication. This middleware can be used for
    global token verification if needed.
    """
    # Skip auth for login endpoint
    if request.url.path in ("/api/auth/login", "/docs", "/openapi.json", "/"):
        return

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )

    token = auth_header.replace("Bearer ", "")
    try:
        jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )
