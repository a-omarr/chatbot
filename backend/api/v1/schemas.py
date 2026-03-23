from __future__ import annotations
from pydantic import BaseModel

class ChatRequest(BaseModel):
    """Payload for incoming chat messages from the user."""
    message: str
    language: str | None = None  # UI-selected language hint (en, tr, ar, ru)

class ChatResponse(BaseModel):
    """Structure for the chatbot's response sent back to the frontend."""
    reply: str
    language: str | None = None
    suggestions: list[str] | None = None
    language_warning: str | None = None
    is_mismatch: bool = False
    suggested_language: str | None = None
    resource_url: str | None = None
