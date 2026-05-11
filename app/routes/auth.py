import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status

from app.database import get_database
from app.models import AuthLoginRequest, AuthLoginResponse

router = APIRouter()

SESSION_DURATION_MINUTES = int(os.getenv("AUTH_SESSION_DURATION_MINUTES", "60"))


@router.post("/auth/login", response_model=AuthLoginResponse, status_code=status.HTTP_200_OK)
async def login(payload: AuthLoginRequest):
    expected_user_id = os.getenv("AUTH_USER_ID")
    expected_password_hash = os.getenv("AUTH_PASSWORD_HASH")

    if not expected_user_id or not expected_password_hash:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Auth credentials are not configured on server."
        )
    # print("pay", payload)
    if payload.user_id != expected_user_id or payload.hash_password != expected_password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials."
        )

    db = get_database()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection is not initialized."
        )

    token = secrets.token_urlsafe(48)
    ist_timezone = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist_timezone)
    expires_at = now + timedelta(minutes=SESSION_DURATION_MINUTES)

    await db.auth_sessions.insert_one(
        {
            "token": token,
            "user_id": payload.user_id,
            "created_at": now,
            "expires_at": expires_at,
        }
    )

    return AuthLoginResponse(
        access_token=token,
        expires_in=SESSION_DURATION_MINUTES * 60,
    )
