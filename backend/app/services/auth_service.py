"""
Authentication service — business logic layer.

COBOL origin: Maps COSGN00C PROCEDURE DIVISION, specifically:
    PROCESS-ENTER-KEY paragraph (lines 118–183):
        1. MOVE FUNCTION TRIM(USERIDI) TO WS-USER-ID
        2. IF WS-USER-ID = SPACES → error
        3. EXEC CICS READ DATASET(USRSEC) RIDFLD(WS-USER-ID) RESP
        4. IF RESP = NOTFND → 'Invalid User ID or Password'
        5. IF SEC-USR-PWD != WS-USER-PWD → 'Invalid User ID or Password'
        6. MOVE SEC-USR-TYPE TO CDEMO-USER-TYPE
        7. IF SEC-USR-TYPE = 'A' → XCTL COADM01C
           ELSE → XCTL COMEN01C

Security improvement: uniform 401 for both user-not-found and wrong-password
prevents user enumeration (original COBOL used different internal paths but
same message string — this is preserved by design).
"""

from fastapi import HTTPException, status

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, LoginResponse
from app.utils.security import create_access_token, verify_password


class AuthService:
    """
    Authentication business logic.

    COBOL source: COSGN00C (Transaction: CC00)
    All CICS XCTL routing decisions are encoded here as redirect_to values
    returned in the LoginResponse — the frontend implements the actual navigation.
    """

    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def authenticate_user(self, request: LoginRequest) -> LoginResponse:
        """
        Authenticate a user and issue a JWT token.

        COBOL origin: COSGN00C PROCESS-ENTER-KEY paragraph.
        Preserves exact error message semantics: same error for user-not-found
        and wrong-password (prevents user enumeration — matches COBOL behavior).

        Steps:
        1. Strip whitespace from user_id (maps: FUNCTION TRIM(USERIDI) → WS-USER-ID)
        2. Validate non-blank user_id (maps: IF WS-USER-ID = SPACES → error)
        3. Look up user in users table (maps: EXEC CICS READ DATASET(USRSEC))
        4. If not found: raise 401 (maps: IF RESP = NOTFND → error message)
        5. Verify password with bcrypt (maps: IF SEC-USR-PWD != WS-USER-PWD)
        6. If mismatch: raise 401 (same message as step 4 — no enumeration)
        7. Determine redirect based on user_type (maps: CICS XCTL routing)
        8. Generate JWT and return LoginResponse
        """
        user_id = request.user_id.strip()

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error_code": "USERID_REQUIRED",
                    "message": "User ID can NOT be empty",
                },
            )

        user = await self._fetch_user(user_id)
        self._verify_credentials(request.password, user)

        access_token = create_access_token(
            subject=user.user_id,
            user_type=user.user_type,
        )

        redirect_to = self._determine_redirect(user.user_type)

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=3600,
            user_id=user.user_id,
            user_type=user.user_type,
            first_name=user.first_name,
            last_name=user.last_name,
            redirect_to=redirect_to,
        )

    async def _fetch_user(self, user_id: str) -> User:
        """
        Fetch user from repository.

        COBOL: EXEC CICS READ DATASET(USRSEC) RIDFLD(WS-USER-ID) RESP RESP2
        RESP=NOTFND (13) → uniform 401 (same message as wrong password).
        """
        user = await self.user_repository.get_by_id(user_id)
        if user is None:
            raise self._invalid_credentials_error()
        return user

    def _verify_credentials(self, plain_password: str, user: User) -> None:
        """
        Verify password against bcrypt hash.

        COBOL: IF PASSWDI = SEC-USR-PWD (plain-text byte comparison)
        Modern: bcrypt constant-time verification (timing-safe; prevents side channels).

        Security note: Same exception as _fetch_user — prevents user enumeration.
        """
        if not verify_password(plain_password, user.password_hash):
            raise self._invalid_credentials_error()

    def _determine_redirect(self, user_type: str) -> str:
        """
        Determine the frontend redirect URL based on user type.

        COBOL origin: COSGN00C PROCESS-ENTER-KEY routing logic:
            IF CDEMO-USRTYP-ADMIN:
                EXEC CICS XCTL PROGRAM('COADM01C') → maps to '/admin/menu'
            ELSE:
                EXEC CICS XCTL PROGRAM('COMEN01C') → maps to '/menu'
        """
        if user_type == "A":
            return "/admin/menu"
        return "/menu"

    @staticmethod
    def _invalid_credentials_error() -> HTTPException:
        """
        Build the uniform 401 exception used for both not-found and wrong-password.

        Security design: identical response prevents user enumeration attacks.
        Preserves COBOL behavior: same WS-MESSAGE for NOTFND and password mismatch.
        """
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_CREDENTIALS",
                "message": "Invalid User ID or Password",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
