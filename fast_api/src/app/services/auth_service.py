"""Authentication service — business logic from COSGN00C.

Maps COBOL paragraphs:
  PROCESS-ENTER-KEY     → authenticate()
  READ-USER-SEC-FILE    → _lookup_and_verify()
  POPULATE-HEADER-INFO  → _build_login_response()

Business rules preserved:
  BR-001: User ID required (validated in schema — raises 422 before service)
  BR-002: Password required (validated in schema — raises 422 before service)
  BR-003: Both fields uppercased before lookup/comparison
  BR-004: User must exist in USRSEC (returns 401 with "User not found" message)
  BR-005: Password must match exactly (returns 401 with "Wrong Password" message)
  BR-006: User type determines redirect destination (admin → /admin-menu, user → /main-menu)
"""
import logging
from datetime import UTC, datetime

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, LoginResponse, TokenPayload, UserInfo
from app.utils.security import create_access_token, verify_password

logger = logging.getLogger(__name__)

# COBOL message constants (from CSMSG01Y.cpy / inline strings in COSGN00C)
_MSG_USER_NOT_FOUND = "User not found. Try again ..."
_MSG_WRONG_PASSWORD = "Wrong Password. Try again ..."
_MSG_SYSTEM_ERROR = "Unable to verify the User ..."


class AuthenticationError(Exception):
    """Raised when authentication fails — maps to RESP 13 or password mismatch."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class AuthService:
    """Implements COSGN00C authentication logic as a service.

    All COBOL paragraph logic is represented here.
    Routers only handle HTTP concerns.
    """

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def authenticate(self, request: LoginRequest) -> LoginResponse:
        """Authenticate user credentials and return a JWT token with routing info.

        Corresponds to COSGN00C PROCESS-ENTER-KEY → READ-USER-SEC-FILE flow.

        BR-003: Uppercase both fields before any comparison.
        BR-004: RESP=13 (not found) → AuthenticationError with user-not-found message.
        BR-005: Password mismatch → AuthenticationError with wrong-password message.
        BR-006: user_type='A' → /admin-menu; user_type='U' → /main-menu.
        """
        # BR-003: Uppercase input (FUNCTION UPPER-CASE in COBOL)
        user_id = request.user_id.upper().strip()
        password = request.password.upper().strip()

        user = await self._lookup_user(user_id)
        self._verify_password(password, user)

        return self._build_login_response(user)

    async def _lookup_user(self, user_id: str) -> User:
        """Fetch user from database — maps EXEC CICS READ DATASET('USRSEC').

        BR-004: raises AuthenticationError when user not found (RESP=13 equivalent).
        """
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            logger.info("Login attempt for unknown user_id: %s", user_id)
            raise AuthenticationError(_MSG_USER_NOT_FOUND)
        return user

    def _verify_password(self, plain_password: str, user: User) -> None:
        """Verify password — maps COBOL: IF SEC-USR-PWD = WS-USER-PWD.

        BR-005: raises AuthenticationError on mismatch.
        """
        if not verify_password(plain_password, user.password):
            logger.info("Failed password attempt for user_id: %s", user.user_id)
            raise AuthenticationError(_MSG_WRONG_PASSWORD)

    def _build_login_response(self, user: User) -> LoginResponse:
        """Build token and routing response — maps COMMAREA population + XCTL routing.

        BR-006: Admin users go to /admin-menu, regular users to /main-menu.
        Maps COBOL:
          MOVE WS-USER-ID    TO CDEMO-USER-ID
          MOVE SEC-USR-TYPE  TO CDEMO-USER-TYPE
          MOVE ZEROS         TO CDEMO-PGM-CONTEXT
          IF CDEMO-USRTYP-ADMIN  XCTL COADM01C
          ELSE                   XCTL COMEN01C
        """
        redirect_to = "/admin-menu" if user.is_admin else "/main-menu"

        token_payload = TokenPayload(
            sub=user.user_id,
            user_type=user.user_type,
            first_name=user.first_name,
            last_name=user.last_name,
        )
        access_token = create_access_token(token_payload)

        user_info = UserInfo(
            user_id=user.user_id,
            first_name=user.first_name,
            last_name=user.last_name,
            user_type=user.user_type,
        )

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_info,
            redirect_to=redirect_to,
            server_time=datetime.now(UTC),
        )
