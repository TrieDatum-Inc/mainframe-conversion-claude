"""
Authentication service — all business logic for login and logout.

COBOL origin: COSGN00C PROCEDURE DIVISION paragraphs:
  - login()  → PROCESS-ENTER-KEY (lines 118-183)
  - logout() → RETURN-TO-PREV-SCREEN (lines 188-200)

Key security decisions preserved from the COBOL analysis:
  1. User-not-found and wrong-password both return IDENTICAL 401 responses.
     The COBOL program displayed the same "Invalid User ID or Password" message
     for both RESP=NOTFND and password mismatch. This correctly prevents user
     enumeration attacks. The modern API maintains this behaviour.
  2. Passwords are verified via bcrypt (constant-time) replacing plain-text
     byte comparison (IF CDEMO-SIGNON-PASSWD = SEC-USR-PWD).
  3. Successful login returns a JWT with user_type claim, replacing the
     CARDDEMO-COMMAREA that was passed via CICS XCTL.
  4. Logout revokes the JWT's jti, replacing the bare EXEC CICS RETURN
     (no TRANSID) that terminated the CICS task.
"""

import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, LoginResponse
from app.utils.security import (
    verify_password,
    create_access_token,
    revoke_token,
)

logger = structlog.get_logger(__name__)
audit_log = structlog.get_logger("audit")

# Uniform credentials error — identical for user-not-found AND wrong password.
# COBOL origin: same WS-MESSAGE displayed for NOTFND and password mismatch.
# Purpose: prevents user enumeration (attacker cannot distinguish the two cases).
_INVALID_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail={
        "error_code": "INVALID_CREDENTIALS",
        "message": "Invalid User ID or Password",
    },
    headers={"WWW-Authenticate": "Bearer"},
)


class AuthService:
    """Business logic for authentication operations."""

    @staticmethod
    async def login(
        request: LoginRequest,
        db: AsyncSession,
        client_ip: str = "unknown",
    ) -> LoginResponse:
        """
        Authenticate a user and issue a JWT access token.

        COBOL origin: COSGN00C PROCESS-ENTER-KEY paragraph.

        Steps (mirroring COBOL logic):
          1. Trim user_id (FUNCTION TRIM already applied by Pydantic validator)
          2. Lookup user in users table (EXEC CICS READ FILE USRSEC RIDFLD)
          3. If not found → 401 INVALID_CREDENTIALS (RESP=NOTFND path)
          4. Verify password via bcrypt (replaces IF SEC-USR-PWD = WS-USER-PWD)
          5. If mismatch → 401 INVALID_CREDENTIALS (password mismatch path)
          6. Determine redirect based on user_type (replaces XCTL routing)
          7. Generate JWT (replaces COMMAREA population + CICS RETURN)
          8. Emit audit log events
        """
        user: User | None = await UserRepository.get_by_id(db, request.user_id)

        # SECURITY: Do NOT distinguish "user not found" from "wrong password"
        # in the response. Both return identical 401. Prevents user enumeration.
        if user is None:
            audit_log.warning(
                "LOGIN_FAILURE",
                user_id=request.user_id,
                reason="user_not_found",
                client_ip=client_ip,
            )
            raise _INVALID_CREDENTIALS_EXCEPTION

        if not verify_password(request.password, user.password_hash):
            audit_log.warning(
                "LOGIN_FAILURE",
                user_id=request.user_id,
                reason="wrong_password",
                client_ip=client_ip,
            )
            raise _INVALID_CREDENTIALS_EXCEPTION

        # Determine redirect URL based on user type.
        # COBOL origin: IF SEC-USR-TYPE = 'A' → XCTL COADM01C
        #               ELSE                  → XCTL COMEN01C
        redirect_to = "/admin/menu" if user.user_type == "A" else "/menu"

        access_token = create_access_token(
            subject=user.user_id,
            user_type=user.user_type,
        )

        audit_log.info(
            "LOGIN_SUCCESS",
            user_id=user.user_id,
            user_type=user.user_type,
            redirect_to=redirect_to,
            client_ip=client_ip,
        )

        return LoginResponse(
            access_token=access_token,
            user_id=user.user_id,
            user_type=user.user_type,  # type: ignore[arg-type]
            first_name=user.first_name,
            last_name=user.last_name,
            redirect_to=redirect_to,
        )

    @staticmethod
    async def logout(
        token: str,
        user_id: str,
        client_ip: str = "unknown",
    ) -> None:
        """
        Revoke the current JWT access token.

        COBOL origin: COSGN00C RETURN-TO-PREV-SCREEN paragraph.
        PF3 displayed CCDA-MSG-THANK-YOU then executed bare EXEC CICS RETURN
        (no TRANSID), which terminated the CICS task with no re-entry point.
        The modern equivalent revokes the JWT's jti so it cannot be reused.
        """
        revoke_token(token)

        audit_log.info(
            "LOGOUT",
            user_id=user_id,
            client_ip=client_ip,
        )
