from __future__ import annotations

"""API Router for chatbot interactions.

This module provides the REST API endpoints for the chatbot, 
delegating business logic to the ChatService.
Bad word detection is applied first; banned messages are rejected
before any ML logic runs.
"""

import logging
from fastapi import APIRouter

from app.services.chat_service import chat_service
from app.services.bad_word_service import bad_word_service
from .schemas import ChatRequest, ChatResponse

router = APIRouter()
logger = logging.getLogger(__name__)

# Localized ban messages returned to the user
_BAN_REPLIES: dict[str, str] = {
    "en": "⚠️ Your message contains inappropriate language. Chat has been disabled for 5 minutes.",
    "tr": "⚠️ Mesajınız uygunsuz ifadeler içeriyor. Sohbet 5 dakika süreyle devre dışı bırakıldı.",
    "ar": "⚠️ رسالتك تحتوي على لغة غير لائقة. تم تعطيل المحادثة لمدة 5 دقائق.",
    "ru": "⚠️ Ваше сообщение содержит ненормативную лексику. Чат заблокирован на 5 минут.",
}

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Main chat endpoint.

    Checks for bad words first. If found, returns a ban response immediately.
    Otherwise delegates to ChatService for language detection, intent
    classification, and KB retrieval.
    """
    try:
        result = chat_service.handle_chat(
            message=request.message,
            selected_lang=request.language,
            session_id=request.session_id
        )
        return ChatResponse(**result)
    except Exception as e:
        logger.exception("Error in chat endpoint")
        raise
