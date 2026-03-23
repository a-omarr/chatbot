from __future__ import annotations

import logging
from typing import Final, Any

from app.ml.intent_engine import predict_intent
from app.ml.knowledge_engine import KnowledgeIndex
from app.ml.data_collector import log_failed_example, FailedExample
from app.core.loader import get_config, get_knowledge_base
from app.services.language_service import language_service

logger = logging.getLogger(__name__)

class ChatService:
    """Service for orchestrating the chatbot logic."""

    def __init__(self):
        self.config = get_config()
        self.knowledge_base = get_knowledge_base()
        self.suggestions_by_lang: Final = self.config["suggestions"]
        self.base_url: Final = self.config["base_url"]
        self.intent_resource_paths: Final = self.config["intent_resource_paths"]
        self.fallback_messages: Final = self.config["fallback_messages"]
        self._kb_index: KnowledgeIndex | None = None

    def _normalize(self, text: str) -> str:
        """Normalize text for consistent comparison (lowercase, alphanumeric only)."""
        return "".join(ch.lower() for ch in text.strip() if ch.isalnum() or ch.isspace())

    def _get_kb_index(self) -> KnowledgeIndex:
        if self._kb_index is None:
            self._kb_index = KnowledgeIndex(self.knowledge_base)
            self._kb_index.build()
        return self._kb_index

    def _answer_about_toros(self, language: str) -> str:
        """Return a descriptive overview of Toros Yazılım in the requested language."""
        kb_items = self.knowledge_base.get(language, [])
        for item in kb_items:
            if item.get("title") == "company_overview":
                return item["answer"]
        
        return (
            "Toros Yazılım is a customer-oriented software and IT consulting company founded in 2008. "
            "We offer service integrations, IT consultancy, and custom software solutions."
        )

    def _answer_from_knowledge_base(self, message: str, language: str) -> tuple[str | None, str | None]:
        """Search the knowledge base for a relevant answer using TF-IDF similarity."""
        index = self._get_kb_index()
        results = index.retrieve(message, lang=language, top_k=1)
        if not results:
            return None, None

        best = results[0]
        if best["score"] < 0.08:
            return None, None

        if best.get("lang") != language:
            return None, None

        return best["answer"], best.get("title")

    def handle_chat(self, message: str, selected_lang: str | None = None) -> dict[str, Any]:
        """Main chat orchestration logic."""
        message = message or ""
        normalized = self._normalize(message)

        # Detect language if not provided or invalid
        if not selected_lang or selected_lang not in language_service.LOCALES:
            selected_lang = language_service.detect_language(message)

        detected_lang = language_service.detect_language(message)
        is_mismatch = (detected_lang != selected_lang)
        lang_warning = language_service.get_language_warning(detected_lang, selected_lang) if is_mismatch else None
        
        suggestions = self.suggestions_by_lang.get(selected_lang, self.suggestions_by_lang["en"])

        def build_result(reply: str = "", intent: str | None = None) -> dict[str, Any]:
            resource_map = self.intent_resource_paths.get(selected_lang, self.intent_resource_paths["default"])
            path = resource_map.get(intent) if intent else None
            
            url = None
            if path:
                url = path if path.startswith("http") else f"{self.base_url}/{selected_lang}/{path}"

            return {
                "reply": reply,
                "language": selected_lang,
                "suggestions": suggestions,
                "language_warning": lang_warning,
                "is_mismatch": is_mismatch,
                "suggested_language": detected_lang,
                "resource_url": url
            }

        # 1. Rule-based check for identity queries
        if "toros yazilim" in normalized or "toros yazılım" in normalized:
            return build_result(self._answer_about_toros(selected_lang), intent="company_overview")

        # 2. Intent Engine (ML model prediction)
        intent_label, confidence = predict_intent(message)

        # 3. High-confidence lookup in Knowledge Base
        if confidence >= 0.10:
            kb_items = self.knowledge_base.get(selected_lang, [])
            for item in kb_items:
                if item.get("title") == intent_label:
                    return build_result(item["answer"], intent=str(intent_label))

        # 4. Fallback to Similarity-based Knowledge Retrieval (RAG)
        kb_answer, kb_intent = self._answer_from_knowledge_base(message, selected_lang)
        if kb_answer:
            return build_result(kb_answer, intent=kb_intent)

        # 5. Final Fallback
        if is_mismatch:
            reply_text = ""
        else:
            reply_text = self.fallback_messages.get(selected_lang, self.fallback_messages["en"])
            log_failed_example(FailedExample(
                text=message,
                predicted_intent=str(intent_label),
                language=selected_lang,
                model_confidence=float(confidence)
            ))

        return build_result(reply_text)

chat_service = ChatService()
