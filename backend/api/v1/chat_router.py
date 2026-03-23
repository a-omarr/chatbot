from __future__ import annotations

"""API Router for chatbot interactions.

This module provides the REST API endpoints for the chatbot, 
delegating business logic to the ChatService.
"""

import logging
from fastapi import APIRouter

from app.services.chat_service import chat_service
from .schemas import ChatRequest, ChatResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Main chat endpoint. 
    
    Delegates language detection, intent classification, and KB retrieval 
    to the ChatService.
    """
    try:
        result = chat_service.handle_chat(
            message=request.message, 
            selected_lang=request.language
        )
        return ChatResponse(**result)
    except Exception as e:
        logger.exception("Error in chat endpoint")
        # In a real app, we might return a more specific 500 error
        raise
