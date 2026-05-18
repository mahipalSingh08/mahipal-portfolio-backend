"""
Centralized OpenAI service for portfolio chatbot.

Handles:
- OpenAI client initialization
- System prompt construction from context file
- Chat completion requests (streaming and non-streaming)
- Token usage logging
- Conversation history management via MongoDB
- Graceful fallback when API key is missing or API call fails
"""
import json
import logging
from datetime import datetime, timezone
from typing import AsyncGenerator, List

from openai import AsyncOpenAI

from app.config import get_settings
from app.database import get_database

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONTEXT_FILE = "mahipal_context.txt"

FALLBACK_RESPONSE = "thanks for message me"

# ---------------------------------------------------------------------------
# Client singleton
# ---------------------------------------------------------------------------

_client: AsyncOpenAI | None = None
_client_available: bool = True


def get_openai_client() -> AsyncOpenAI | None:
    """Return a singleton AsyncOpenAI client, or None if not configured."""
    global _client, _client_available
    if _client is None and _client_available:
        settings = get_settings()
        if not settings.openai_api_key:
            logger.warning("OPENAI_API_KEY is not configured — will use fallback responses.")
            _client_available = False
            return None
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


# ---------------------------------------------------------------------------
# Context loader
# ---------------------------------------------------------------------------

_context: str | None = None


def load_context() -> str:
    """Load and cache the Mahipal Singh context from the text file."""
    global _context
    if _context is not None:
        return _context

    try:
        with open(CONTEXT_FILE, encoding="utf-8") as f:
            _context = f.read().strip()
        logger.info("Loaded context from '%s' (%d chars)", CONTEXT_FILE, len(_context))
    except FileNotFoundError:
        logger.warning("Context file '%s' not found — using fallback.", CONTEXT_FILE)
        _context = (
            "Mahipal Singh is an engineer and AI-focused developer "
            "who builds applications using Python, Angular, OpenAI, and MongoDB."
        )
    except Exception:
        logger.exception("Failed to load context file.")
        _context = ""
    return _context or ""


def build_system_prompt() -> str:
    """
    Build the system prompt that instructs the AI to act as Mahipal Singh.
    """
    context = load_context()
    return (
        "You are Mahipal Singh, an engineer and AI-focused developer. "
        "You are having a conversation with someone visiting your portfolio website.\n\n"
        "INSTRUCTIONS:\n"
        "1. Answer professionally and concisely (2-4 sentences is usually enough).\n"
        "2. Use the context below to mention your skills, projects, and experience.\n"
        "3. If asked something outside the provided context, say: "
        '"I don\'t have information about that yet."\n'
        "4. Encourage users to explore your projects on GitHub or your portfolio website.\n"
        "5. Keep a friendly, modern developer tone.\n"
        "6. Do NOT invent facts — stay truthful to the provided context.\n\n"
        "CONTEXT:\n"
        f"{context}"
    )


# ---------------------------------------------------------------------------
# Conversation memory (MongoDB-backed, per-session)
# ---------------------------------------------------------------------------

COLLECTION = "chat_sessions"
MAX_HISTORY = 10


class ConversationStore:
    """
    Persistent chat history store backed by MongoDB.

    Each document in the ``chat_sessions`` collection has the shape::

        {
            "session_id": str,
            "created_at": ISODate,           # set on first insert; TTL index
            "messages": [                     # last MAX_HISTORY messages
                {"role": str, "content": str},
                ...
            ]
        }

    Documents auto-expire 6 months after ``created_at`` via a TTL index.
    """

    @staticmethod
    def _db():
        return get_database()

    async def get_history(self, session_id: str) -> list[dict]:
        db = self._db()
        if db is None:
            logger.warning("MongoDB not available — returning empty history.")
            return []
        doc = await db[COLLECTION].find_one(
            {"session_id": session_id},
            projection={"_id": False, "messages": True},
        )
        return doc["messages"] if doc else []

    async def add_message(self, session_id: str, role: str, content: str) -> None:
        db = self._db()
        if db is None:
            logger.warning("MongoDB not available — cannot persist message.")
            return

        now = datetime.now(timezone.utc)

        # Use an upsert: find the session and push the new message,
        # or create the document if it doesn't exist yet.
        result = await db[COLLECTION].update_one(
            {"session_id": session_id},
            {
                "$push": {"messages": {"role": role, "content": content}},
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )

        # If the document already existed, update created_at on first insert only
        # (TTL is based on created_at, so don't bump it on every message).

        # Trim the message array to MAX_HISTORY using an aggregation / update pipeline.
        # We need to check if the array exceeds the limit after push.
        if result.upserted_id is None:
            # Document already existed — trim array if needed
            await db[COLLECTION].update_one(
                {"session_id": session_id},
                [
                    {
                        "$set": {
                            "messages": {
                                "$cond": [
                                    {"$gt": [{"$size": "$messages"}, MAX_HISTORY]},
                                    {"$slice": ["$messages", -MAX_HISTORY]},
                                    "$messages",
                                ]
                            }
                        }
                    }
                ],
            )

    async def clear(self, session_id: str) -> None:
        db = self._db()
        if db is None:
            return
        await db[COLLECTION].delete_one({"session_id": session_id})

    async def create_session(self, session_id: str) -> None:
        """Create a new empty session document (no-op if already exists)."""
        db = self._db()
        if db is None:
            logger.warning("MongoDB not available — cannot create session.")
            return
        await db[COLLECTION].update_one(
            {"session_id": session_id},
            {
                "$setOnInsert": {
                    "created_at": datetime.now(timezone.utc),
                    "messages": [],
                }
            },
            upsert=True,
        )


# Global conversation store instance
conversation_store = ConversationStore()


# ---------------------------------------------------------------------------
# Main service
# ---------------------------------------------------------------------------


async def get_chat_response(
    message: str,
    session_id: str | None = None,
    *,
    stream: bool = False,
) -> str | AsyncGenerator[str, None]:
    """
    Send a chat message to OpenAI and return/stream the response.

    Parameters
    ----------
    message : str
        The user's message.
    session_id : str | None
        Optional session ID for maintaining conversation history.
    stream : bool
        If True, returns an async generator yielding response chunks.

    Returns
    -------
    str or AsyncGenerator[str, None]
        The AI response as a string or a stream of chunks.
    """
    from app.config import get_settings

    settings = get_settings()
    client = get_openai_client()

    # Graceful fallback when OpenAI client is not available
    if client is None:
        logger.info("OpenAI client unavailable — returning fallback response.")
        if stream:
            return _fallback_stream_response(session_id)
        else:
            return _fallback_complete_response(session_id)

    system_prompt = build_system_prompt()

    # Build message list with history
    messages: list[dict] = [{"role": "system", "content": system_prompt}]

    if session_id:
        # Inject conversation history (excluding system prompt)
        history = await conversation_store.get_history(session_id)
        messages.extend(history)

    # Add the new user message
    messages.append({"role": "user", "content": message})

    # Save user message to history
    if session_id:
        await conversation_store.add_message(session_id, "user", message)

    try:
        if stream:
            return _stream_response(client, messages, settings, session_id)
        else:
            return await _complete_response(client, messages, settings, session_id)
    except Exception:
        logger.exception("OpenAI API call failed — returning fallback response.")
        # Graceful fallback on API failure
        if stream:
            return _fallback_stream_response(session_id)
        else:
            return _fallback_complete_response(session_id)


# ---------------------------------------------------------------------------
# Fallback responses (when OpenAI API key is missing or API call fails)
# ---------------------------------------------------------------------------


def _fallback_complete_response(session_id: str | None) -> str:
    """Return fallback response for non-streaming mode."""
    if session_id:
        # Fire-and-forget style; we can't await in a sync generator.
        import asyncio
        asyncio.ensure_future(
            conversation_store.add_message(session_id, "assistant", FALLBACK_RESPONSE)
        )
    return FALLBACK_RESPONSE


def _fallback_stream_response(session_id: str | None) -> AsyncGenerator[str, None]:
    """Return fallback response for streaming mode."""

    async def _generate():
        yield FALLBACK_RESPONSE
        if session_id:
            await conversation_store.add_message(session_id, "assistant", FALLBACK_RESPONSE)

    return _generate()


# ---------------------------------------------------------------------------
# OpenAI completions
# ---------------------------------------------------------------------------


async def _complete_response(
    client: AsyncOpenAI,
    messages: list[dict],
    settings,
    session_id: str | None,
) -> str:
    """Non-streaming chat completion."""
    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
        max_tokens=settings.openai_max_tokens,
        temperature=settings.openai_temperature,
    )

    content = response.choices[0].message.content or ""

    # Log token usage
    if response.usage:
        _log_token_usage(
            session_id or "anonymous",
            response.usage.prompt_tokens,
            response.usage.completion_tokens,
        )

    # Save assistant response to history
    if session_id:
        await conversation_store.add_message(session_id, "assistant", content)

    return content


async def _stream_response(
    client: AsyncOpenAI,
    messages: list[dict],
    settings,
    session_id: str | None,
) -> AsyncGenerator[str, None]:
    """Streaming chat completion — yields content chunks."""
    stream = await client.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
        max_tokens=settings.openai_max_tokens,
        temperature=settings.openai_temperature,
        stream=True,
        stream_options={"include_usage": True},
    )

    full_content: list[str] = []
    usage_data = None

    async for chunk in stream:
        delta = chunk.choices[0].delta if chunk.choices else None
        if delta and delta.content:
            full_content.append(delta.content)
            yield delta.content

        # Capture usage from the final chunk
        if hasattr(chunk, "usage") and chunk.usage:
            usage_data = chunk.usage

    if usage_data:
        _log_token_usage(
            session_id or "anonymous",
            usage_data.prompt_tokens or 0,
            usage_data.completion_tokens or 0,
        )

    # Save assistant response to history
    if session_id:
        await conversation_store.add_message(session_id, "assistant", "".join(full_content))


# ---------------------------------------------------------------------------
# Token usage logging
# ---------------------------------------------------------------------------


def _log_token_usage(
    session_id: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> None:
    """Log token usage with timestamp for monitoring/cost tracking."""
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "model": get_settings().openai_model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }
    logger.info("Token usage: %s", json.dumps(record))