from __future__ import annotations

"""API Router for chatbot interactions.

This module handles incoming chat requests, performs language detection,
intent classification, and retrieves relevant answers from the knowledge base.
"""

import logging
import re
from typing import Any, Final

from fastapi import APIRouter
from pydantic import BaseModel

from app.ml.intent_engine import predict_intent
from app.ml.knowledge_engine import KnowledgeIndex
from app.ml.data_collector import log_failed_example, FailedExample
from app.core.loader import get_config, get_knowledge_base

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Initialization & Data Loading
# ---------------------------------------------------------------------------

router = APIRouter()
logger = logging.getLogger(__name__)

# Load configuration and knowledge base from JSON
config = get_config()
KNOWLEDGE_BASE = get_knowledge_base()

SUGGESTIONS_BY_LANG: Final = config["suggestions"]
BASE_URL: Final = config["base_url"]
INTENT_RESOURCE_PATHS: Final = config["intent_resource_paths"]
FALLBACK_MESSAGES: Final = config["fallback_messages"]

# Global cross-lingual retriever (lazy-built on first call)
_kb_index: KnowledgeIndex | None = None

# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    """Normalize text for consistent comparison (lowercase, alphanumeric only)."""
    return "".join(ch.lower() for ch in text.strip() if ch.isalnum() or ch.isspace())

def _answer_about_toros(language: str) -> str:
    """Return a descriptive overview of Toros Yazılım in the requested language."""
    # Try to get it from the knowledge base first
    kb_items = KNOWLEDGE_BASE.get(language, [])
    for item in kb_items:
        if item.get("title") == "company_overview":
            return item["answer"]
    
    # Fallback if not in KB (English default)
    return (
        "Toros Yazılım is a customer-oriented software and IT consulting company founded in 2008. "
        "We offer service integrations, IT consultancy, and custom software solutions."
    )

def _answer_from_knowledge_base(message: str, language: str) -> tuple[str | None, str | None]:
    """Search the knowledge base for a relevant answer using TF-IDF similarity."""
    global _kb_index
    if _kb_index is None:
        _kb_index = KnowledgeIndex(KNOWLEDGE_BASE)
        _kb_index.build()

    results = _kb_index.retrieve(message, lang=language, top_k=1)
    if not results:
        return None, None

    best = results[0]
    # Similarity threshold to avoid low-quality irrelevant matches
    if best["score"] < 0.08:
        return None, None

    # Ensure we return an answer in the user's selected language
    if best.get("lang") != language:
        return None, None

    return best["answer"], best.get("title")

def _detect_language_from_text(text: str) -> str:
    """Heuristic-based language detection tailored for the supported locales."""
    if not text.strip():
        return "en"

    # Strip domain-specific terms to avoid bias (e.g., 'Toros' shouldn't always trigger TR)
    brand_terms = r"\b(toros|yazilim|kiyos|authnac|makscyber|ari konaklama|siem|demo|api|sso|mfa|edugain)\b"
    clean_text = re.sub(brand_terms, "", text, flags=re.IGNORECASE).lower()

    scores = {"en": 0, "tr": 0, "ar": 0, "ru": 0}

    # Script-based detection (high weight)
    if any("\u0600" <= ch <= "\u06FF" for ch in text): scores["ar"] += 5
    if any("\u0400" <= ch <= "\u04FF" for ch in text): scores["ru"] += 5
    
    tr_chars = ["ç", "ğ", "ı", "ş", "ö", "ü"]
    if any(ch in clean_text for ch in tr_chars): scores["tr"] += 4

    # Keyword-based detection (lower weight)
    tr_keywords = {"merhaba", "selam", "nasıl", "nedir", "nerede", "hakkında", "teşekkür"}
    en_keywords = {"hello", "hi", "how", "what", "where", "about", "thanks"}
    
    words = set(re.findall(r"\w+", clean_text))
    for word in words:
        if word in tr_keywords: scores["tr"] += 2
        if word in en_keywords: scores["en"] += 2

    if max(scores.values()) == 0:
        return "en"

    return max(scores, key=lambda l: scores[l])

def _get_language_warning(detected: str, selected: str) -> str | None:
    """Generate a friendly warning if the detected language differs from the selection."""
    if detected == selected:
        return None
    
    names = {
        "en": {"en": "English", "tr": "İngilizce", "ar": "الإنجليزية", "ru": "Английский"},
        "tr": {"en": "Turkish", "tr": "Türkçe", "ar": "التركية", "ru": "Турецкий"},
        "ar": {"en": "Arabic", "tr": "Arapça", "ar": "العربية", "ru": "Арабский"},
        "ru": {"en": "Russian", "tr": "Rusça", "ar": "الروسية", "ru": "Русский"},
    }
    
    msg_templates = {
        "en": "It looks like you're typing in {lang}. Would you like to switch?",
        "tr": "{lang} dilinde yazıyor gibisiniz. Geçmek ister misiniz?",
        "ar": "يبدو أنك تكتب بـ{lang}. هل تريد التبديل؟",
        "ru": "Похоже, вы печатаете на {lang}. Хотите переключиться?",
    }
    
    lang_name = names.get(detected, {}).get(selected, detected)
    template = msg_templates.get(selected, msg_templates["en"])
    return template.format(lang=lang_name)

# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Main chat endpoint. Handles language, intent, and KB retrieval."""
    message = request.message or ""
    normalized = _normalize(message)

    # Determine language preference
    selected_lang = (request.language or "").lower()
    if selected_lang not in {"en", "tr", "ar", "ru"}:
        selected_lang = _detect_language_from_text(message)

    detected_lang = _detect_language_from_text(message)
    is_mismatch = (detected_lang != selected_lang)
    lang_warning = _get_language_warning(detected_lang, selected_lang) if is_mismatch else None
    
    suggestions = SUGGESTIONS_BY_LANG.get(selected_lang, SUGGESTIONS_BY_LANG["en"])

    def create_response(reply: str = "", intent: str | None = None) -> ChatResponse:
        """Helper to build consistent ChatResponse objects."""
        resource_map = INTENT_RESOURCE_PATHS.get(selected_lang, INTENT_RESOURCE_PATHS["default"])
        path = resource_map.get(intent) if intent else None
        
        url = None
        if path:
            url = path if path.startswith("http") else f"{BASE_URL}/{selected_lang}/{path}"

        return ChatResponse(
            reply=reply,
            language=selected_lang,
            suggestions=suggestions,
            language_warning=lang_warning,
            is_mismatch=is_mismatch,
            suggested_language=detected_lang,
            resource_url=url
        )

    # 1. Rule-based check for identity queries
    if "toros yazilim" in normalized or "toros yazılım" in normalized:
        return create_response(_answer_about_toros(selected_lang), intent="company_overview")

    # 2. Intent Engine (ML model prediction)
    intent_label, confidence = predict_intent(message)

    # 3. High-confidence lookup in Knowledge Base
    if confidence >= 0.10:  # Restore threshold for better intent matching
        kb_items = KNOWLEDGE_BASE.get(selected_lang, [])
        for item in kb_items:
            if item.get("title") == intent_label:
                return create_response(item["answer"], intent=str(intent_label))

    # 4. Fallback to Similarity-based Knowledge Retrieval (RAG)
    kb_answer, kb_intent = _answer_from_knowledge_base(message, selected_lang)
    if kb_answer:
        return create_response(kb_answer, intent=kb_intent)

    # 5. Final Fallback (Localized "I don't know" or log for active learning)
    if is_mismatch:
        reply_text = ""  # Silence on mismatch if no clear answer found
    else:
        reply_text = FALLBACK_MESSAGES.get(selected_lang, FALLBACK_MESSAGES["en"])
        # Log for human review if we failed to find an answer
        log_failed_example(FailedExample(
            text=message,
            predicted_intent=str(intent_label),
            language=selected_lang,
            model_confidence=float(confidence)
        ))

    return create_response(reply_text)
