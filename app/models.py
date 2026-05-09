from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timezone
from typing import List

class ContactForm(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    email: EmailStr = Field(..., max_length=100)
    query: str = Field(..., min_length=10, max_length=1000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DeleteContactsRequest(BaseModel):
    ids: List[str] = Field(..., description="List of MongoDB ObjectIds as strings to delete")
