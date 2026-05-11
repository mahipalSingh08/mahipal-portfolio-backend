from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timezone, timedelta
from typing import List

class ContactForm(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    email: EmailStr = Field(..., max_length=100)
    query: str = Field(..., min_length=10, max_length=1000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone(timedelta(hours=5, minutes=30))))

class DeleteContactsRequest(BaseModel):
    ids: List[str] = Field(..., description="List of MongoDB ObjectIds as strings to delete")


class AuthLoginRequest(BaseModel):
    user_id: str = Field(..., min_length=3, max_length=100, description="Frontend user identifier")
    hash_password: str = Field(..., min_length=20, max_length=500, description="Hashed password from frontend")


class AuthLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
