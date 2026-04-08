"""
Authentication service — business logic from COSGN00C.

Converts COSGN00C signon logic to a Python service:
  MAIN-PARA / PROCESS-ENTER-KEY → authenticate_user()
  READ-USER-SEC-FILE            → _verify_credentials()
  EXEC CICS XCTL (COADM01C/COMEN01C) → return JWT with role claim

JWT creation replaces CICS COMMAREA return:
  EXEC CICS RETURN TRANSID(WS-TRANID) COMMAREA(CARDDEMO-COMMAREA)
  → return TokenResponse with JWT access_token

Business rules preserved from COSGN00C:
  1. User ID is uppercased before lookup (FUNCTION UPPER-CASE)
  2. Both user_id and password must be non-blank
  3. RESP=13 (NOTFND) → "User not found. Try again ..."
  4. Wrong password → "Wrong Password. Try again ..."
  5. User type 'A' → admin role in JWT; others → regular user role
"""
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.repositories.user_repo import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse
from app.utils.cobol_compat import cobol_upper, cobol_spaces_or_low_values
from app.utils.error_handlers import AuthenticationError, RecordNotFoundError

settings = get_settings()


class AuthService:
    """
    Authentication business logic derived from COSGN00C.

    Paragraph mapping:
      PROCESS-ENTER-KEY  → authenticate_user()
      READ-USER-SEC-FILE → _verify_credentials()
    """

    def __init__(self, db: AsyncSession) -> None:
        self._repo = UserRepository(db)

    async def authenticate_user(self, request: LoginRequest) -> TokenResponse:
        """
        Full sign-on flow from COSGN00C PROCESS-ENTER-KEY paragraph.

        Business rules:
          1. User ID uppercased (FUNCTION UPPER-CASE)
          2. User looked up in USRSEC (EXEC CICS READ FILE('USRSEC'))
          3. RESP=13 → "User not found. Try again ..."
          4. Password compared → "Wrong Password. Try again ..."
          5. On success: create JWT with user type as role claim

        Args:
            request: LoginRequest with user_id and password.

        Returns:
            TokenResponse with JWT access token.

        Raises:
            AuthenticationError: Invalid credentials (mirrors COSGN00C error messages).
        """
        # COSGN00C: MOVE FUNCTION UPPER-CASE(USERIDI) TO WS-USER-ID
        user_id_normalized = cobol_upper(request.user_id).strip()

        # EXEC CICS READ FILE('USRSEC') → RecordNotFoundError if not found
        try:
            user = await self._repo.get_by_id(user_id_normalized)
        except RecordNotFoundError:
            # COSGN00C: WHEN 13 → "User not found. Try again ..."
            raise AuthenticationError("User not found. Try again ...")

        # COSGN00C: IF SEC-USR-PWD = WS-USER-PWD ... ELSE → "Wrong Password. Try again ..."
        if not self._verify_password(request.password, user.password_hash):
            raise AuthenticationError("Wrong Password. Try again ...")

        # COSGN00C: MOVE SEC-USR-TYPE TO CDEMO-USER-TYPE
        # IF CDEMO-USRTYP-ADMIN → XCTL COADM01C ELSE → XCTL COMEN01C
        token = self._create_access_token(user_id=user.user_id.strip(), role=user.user_type)

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user_id=user.user_id.strip(),
            user_type=user.user_type,
            first_name=user.first_name,
            last_name=user.last_name,
        )

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        COSGN00C: IF SEC-USR-PWD = WS-USER-PWD

        Original COBOL does direct string comparison (plaintext).
        Modernized to bcrypt hash comparison.
        """
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )

    def _create_access_token(self, user_id: str, role: str) -> str:
        """
        Create JWT replacing CICS COMMAREA (COCOM01Y).

        JWT claims:
          sub  → CDEMO-USER-ID (PIC X(08))
          role → CDEMO-USER-TYPE (PIC X(01))
          exp  → expiration (not in COBOL — new in modernization)
        """
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
        payload = {
            "sub": user_id,
            "role": role,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    @staticmethod
    def hash_password(plain_password: str) -> str:
        """
        Hash a plaintext password for storage.

        Used during user creation (COUSR01C) and password updates (COUSR02C).
        COBOL stores plaintext; we hash with bcrypt at the API boundary.
        """
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")
