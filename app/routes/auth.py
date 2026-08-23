import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status

from app.config import get_settings
from app.database import get_database
from app.models import AuthLoginRequest, AuthLoginResponse

router = APIRouter()
settings = get_settings()


@router.post("/auth/login", response_model=AuthLoginResponse, status_code=status.HTTP_200_OK)
async def login(payload: AuthLoginRequest):
    if not settings.auth_user_id or not settings.auth_password_hash:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Auth credentials are not configured on server."
        )

    valid_user_id = secrets.compare_digest(payload.user_id, settings.auth_user_id)
    valid_password = secrets.compare_digest(payload.hash_password, settings.auth_password_hash)
    if not valid_user_id or not valid_password:
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
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.auth_session_duration_minutes)

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
        expires_in=settings.auth_session_duration_minutes * 30,
    )
