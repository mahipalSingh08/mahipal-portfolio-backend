from pydantic import BaseModel, EmailStr, Field


class ContactForm(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    email: EmailStr = Field(..., max_length=100)
    query: str = Field(..., min_length=10, max_length=1000)
    website: str = Field("", max_length=500, description="Honeypot field - must be empty for real users")


class DeleteContactsRequest(BaseModel):
    ids: list[str] = Field(..., description="List of MongoDB ObjectIds as strings to delete")


class AuthLoginRequest(BaseModel):
    user_id: str = Field(..., min_length=3, max_length=100, description="Frontend user identifier")
    hash_password: str = Field(..., min_length=20, max_length=500, description="Hashed password from frontend")


class AuthLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class Reaction(BaseModel):
    reaction: str
    email: str
    name: str


# ── Chat / AI models ────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """Request model for POST /chat."""
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's message to the AI assistant.",
    )
    session_id: str | None = Field(
        None,
        max_length=100,
        description="Optional session ID for conversation history.",
    )


class ChatResponse(BaseModel):
    """Response model for POST /chat."""
    response: str = Field(..., description="AI assistant's reply.")
    session_id: str | None = Field(None, description="Echoed session ID if provided.")



class CreateSessionResponse(BaseModel):
    """Response model for POST /chat/session."""
    session_id: str = Field(..., description="Newly created or existing session ID.")
    message: str = Field("Session created successfully.", description="Status message.")
