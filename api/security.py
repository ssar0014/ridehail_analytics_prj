from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

from api.config import get_settings
from api.db import PgConn
from api.schemas import CurrentUser
from enums.user_role import UserRole

_hasher = PasswordHash.recommended()
# Verified against when the email doesn't exist, so a login miss costs the same
# as a wrong password and doesn't reveal which emails have accounts.
_DUMMY_HASH = _hasher.hash("not-a-real-password")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    """CPU-bound (argon2) — call via run_in_threadpool from async code."""
    if password_hash is None:
        _hasher.verify(password, _DUMMY_HASH)
        return False
    return _hasher.verify(password, password_hash)


def create_access_token(user_id: UUID, role: UserRole) -> tuple[str, int]:
    settings = get_settings()
    ttl = timedelta(minutes=settings.access_token_ttl_minutes)
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "role": role.value, "iat": now, "exp": now + ttl}
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, int(ttl.total_seconds())


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    conn: PgConn,
) -> CurrentUser:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise _CREDENTIALS_ERROR

    # Re-read the account on every request so deactivation and role changes
    # take effect immediately rather than at token expiry.
    async with conn.cursor() as cur:
        await cur.execute(
            "SELECT user_id, email, role, driver_id, customer_id, is_active "
            "FROM app_users WHERE user_id = %s",
            (user_id,),
        )
        row = await cur.fetchone()
    if row is None or not row["is_active"]:
        raise _CREDENTIALS_ERROR
    return CurrentUser(**row)


def require_role(*roles: UserRole):
    async def dependency(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not permitted for this role")
        return user

    return dependency


AuthedUser = Annotated[CurrentUser, Depends(get_current_user)]
AdminUser = Annotated[CurrentUser, Depends(require_role(UserRole.ADMIN))]
DriverUser = Annotated[CurrentUser, Depends(require_role(UserRole.DRIVER))]
CustomerUser = Annotated[CurrentUser, Depends(require_role(UserRole.CUSTOMER))]
