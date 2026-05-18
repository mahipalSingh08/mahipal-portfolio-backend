"""
Chat / AI assistant route.

Provides:
- POST /chat — Non-streaming chat completion
- GET /chat/all — Retrieve all chat sessions with pagination
- POST /chat/session — Create a new chat session
- GET /chat/history/{session_id} — Retrieve conversation history
- DELETE /chat/history/{session_id} — Clear conversation history
"""
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.limiter import limiter
from app.models import ChatRequest, ChatResponse, CreateSessionResponse
from app.services.openai_service import (
    conversation_store,
    get_chat_response,
)
from app.verifyToken import verify_access_token

logger = logging.getLogger(__name__)

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# POST /chat/session — Create a new session (intentional, stable session_id)
# ─────────────────────────────────────────────────────────────────────────────


@router.post(
    "/chat/session",
    response_model=CreateSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new chat session",
    description="Generates a unique session_id and initializes it in the persistent store. "
    "The frontend should store this ID and pass it with every subsequent chat request.",
)
async def create_session():
    """Explicitly create a chat session so the frontend gets a stable session_id
    that persists across page reloads (by storing it in localStorage)."""
    session_id = str(uuid.uuid4())
    await conversation_store.create_session(session_id)
    logger.info("Created chat session: %s", session_id)
    return CreateSessionResponse(
        session_id=session_id,
        message="Chat session created successfully.",
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /chat — Non-streaming
# ─────────────────────────────────────────────────────────────────────────────


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a chat message to the AI assistant",
    description="Sends a user message with optional session_id for conversation history. Returns the AI response.",
)
@limiter.limit("20 per hour")
async def chat(body: ChatRequest, request: Request):
    try:
        # Generate a session_id if none was provided, so the frontend
        # gets one back and can pass it in subsequent requests.
        session_id = body.session_id or str(uuid.uuid4())

        response_text = await get_chat_response(
            message=body.message,
            session_id=session_id,
            stream=False,
        )
        return ChatResponse(response=response_text, session_id=session_id)
    except Exception:
        logger.exception("Chat endpoint failed unexpectedly.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get AI response. Please try again later.",
        )


# ─────────────────────────────────────────────────────────────────────────────
# GET /chat/all — Paginated chat retrieval
# ─────────────────────────────────────────────────────────────────────────────


@router.get(
    "/chat/all",
    status_code=status.HTTP_200_OK,
    summary="Get all chat sessions with pagination",
    description="Retrieve all chat sessions including their history. Admin authentication required.",
)
async def get_all_chats(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    _: bool = Depends(verify_access_token),
):
    from app.database import get_database
    from datetime import datetime, timezone

    db = get_database()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection is not initialized."
        )

    skip = (page - 1) * limit

    try:
        cursor = db["chat_sessions"].find().sort([("created_at", -1)]).skip(skip).limit(limit)
        sessions = await cursor.to_list(length=limit)

        total_sessions = await db["chat_sessions"].count_documents({})

        formatted_sessions = []
        for session in sessions:
            session["_id"] = str(session["_id"])

            created_at = session.get("created_at")
            if created_at and isinstance(created_at, datetime):
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                session["created_at"] = created_at

            formatted_sessions.append(session)

        return {
            "data": formatted_sessions,
            "pagination": {
                "total": total_sessions,
                "page": page,
                "limit": limit,
                "total_pages": (total_sessions + limit - 1) // limit
            }
        }
    except Exception as e:
        logger.exception("Failed to retrieve chat sessions.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat sessions."
        ) from e


# ─────────────────────────────────────────────────────────────────────────────
# History management
# ─────────────────────────────────────────────────────────────────────────────


@router.get(
    "/chat/history/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Get conversation history for a session",
)
async def get_history(session_id: str):
    history = await conversation_store.get_history(session_id)
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No conversation history found for this session.",
        )
    return {"session_id": session_id, "history": history}


@router.delete(
    "/chat/history/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Clear conversation history for a session",
)
async def clear_history(session_id: str):
    await conversation_store.clear(session_id)
    return {"message": f"Conversation history for session '{session_id}' cleared."}