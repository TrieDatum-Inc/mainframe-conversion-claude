"""
Auth service — COSGN00C login/logout business logic.

COBOL origin: COSGN00C PROCESS-ENTER-KEY paragraph.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.exceptions.errors import InvalidCredentialsError
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginResponse
from app.utils.security import create_access_token, verify_password


async def login(user_id: str, password: str, db: AsyncSession) -> LoginResponse:
    """
    Authenticate user and return JWT token.

    COSGN00C PROCESS-ENTER-KEY:
      1. EXEC CICS READ DATASET(USRSEC) RIDFLD(user_id)
         IF RESP=NOTFND → 'Invalid User ID or Password'
      2. IF SEC-USR-PWD != password → 'Invalid User ID or Password'
      3. SET CDEMO-USER-TYPE, CDEMO-USER-ID in COMMAREA
      4. EXEC CICS XCTL PROGRAM('COADM01C' or 'COMEN01C')

    Here: verify bcrypt hash, return JWT, return redirect_to URL.
    """
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id.strip())

    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError()

    token = create_access_token(subject=user.user_id, user_type=user.user_type)
    redirect_to = "/admin/menu" if user.user_type == "A" else "/menu"

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.jwt_expire_minutes * 60,
        user_id=user.user_id,
        user_type=user.user_type,
        first_name=user.first_name,
        last_name=user.last_name,
        redirect_to=redirect_to,
    )
