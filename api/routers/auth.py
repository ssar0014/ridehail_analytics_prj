from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from fastapi.security import OAuth2PasswordRequestForm

from api.db import PgConn
from api.schemas import CurrentUser, Token
from api.security import AuthedUser, create_access_token, verify_password
from enums.user_role import UserRole

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], conn: PgConn) -> Token:
    """OAuth2 password flow — `username` is the account email."""
    async with conn.cursor() as cur:
        await cur.execute(
            "SELECT user_id, role, password_hash, is_active FROM app_users WHERE email = %s",
            (form.username.strip().lower(),),
        )
        row = await cur.fetchone()

    ok = await run_in_threadpool(verify_password, form.password, row["password_hash"] if row else None)
    if not ok or not row["is_active"]:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    async with conn.cursor() as cur:
        await cur.execute("UPDATE app_users SET last_login_at = NOW() WHERE user_id = %s", (row["user_id"],))

    token, expires_in = create_access_token(row["user_id"], UserRole(row["role"]))
    return Token(access_token=token, expires_in=expires_in)


@router.get("/me", response_model=CurrentUser)
async def me(user: AuthedUser) -> CurrentUser:
    return user
