from __future__ import annotations

import logging
from typing import Final, Any

from app.ml.intent_engine import predict_intent, predict_top_k
from app.ml.knowledge_engine import KnowledgeIndex
from app.ml.data_collector import log_failed_example, FailedExample
from app.ml.slot_extractor import extract_slot
from app.core.loader import get_config, get_knowledge_base
from app.services.language_service import language_service
from app.services.memory_store import memory_store
from app.services.bad_word_service import bad_word_service

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
        """Normalize text for consistent comparison (lowercase, accent-insensitive)."""
        if not text:
            return ""
        text = text.lower()
        replacements = {
            "ı": "i", "İ": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g",
            "ü": "u", "Ü": "u", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c"
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return "".join(ch for ch in text.strip() if ch.isalnum() or ch.isspace())

    def _get_kb_index(self) -> KnowledgeIndex:
        if self._kb_index is None:
            self._kb_index = KnowledgeIndex(self.knowledge_base)
            self._kb_index.build()
        return self._kb_index

    def _is_answer_grounded(self, query: str, answer: str, intent: str | None = None) -> bool:
        """Heuristic to check if the answer is relevant to the question."""
        answer_lower = answer.lower()
        normalized_query = self._normalize(query)
        query_words = [w for w in normalized_query.split() if len(w) > 3]
        
        # Identity keywords
        identity_keywords = ["toros", "yazilim", "yazılım", "siem", "maks", "cyber", "kiyos", "authnac"]
        
        # Multilingual whitelist of keywords per intent
        topic_keywords = {
            "founding_year": ["founded", "establish", "year", "2008", "kurul", "ne zaman", "kurulus", "kuruluş", "تأسس", "основан"],
            "working_hours": ["hours", "open", "close", "time", "saat", "mesai", "kacta", "kaçta", "ساعات", "работает"],
            "location": ["where", "address", "city", "located", "nerede", "adres", "konum", "ofis", "أين", "مكتب", "где", "адрес"],
            "mission": ["mission", "goal", "aim", "misyon", "hedef", "amac", "amaç", "مهمة", "миссия"],
            "vision": ["vision", "future", "vizyon", "gelecek", "hedef", "رؤية", "видение"],
            "services": ["service", "offer", "provide", "solutions", "hizmet", "neler yap", "خدمات", "услуги"],
            "products": ["product", "software", "solution", "urun", "ürün", "neler", "منتجات", "продукты"],
            "contact_info": ["contact", "reach", "email", "phone", "iletisim", "iletişim", "numara", "bilgi", "اتصل", "رقم", "هاتف", "تليفون", "تلفون", "تليفونكم", "связаться", "номер"],
            "it_consultancy": ["it", "consulting", "consultancy", "expert", "danisman", "danışman", "proje", "yazilim", "استشارات", "консалтинг"],
            "makscyber_siem": ["siem", "security", "threat", "cyber", "maks", "siber", "guvenlik", "güvenlik", "günlük", "أمن", "безопасность"],
            "kiyos_features": ["kiyos", "ldap", "identity", "auth", "sso", "kimlik", "erisim", "erişim", "ميزات", "функции"],
            "request_demo": ["demo", "quote", "price", "cost", "trial", "teklif", "fiyat", "deneme", "تجريبي", "سعر", "демо"],
            "career_info": ["job", "career", "work", "apply", "hiring", "is ", "iş ", "basvuru", "başvuru", "ise alim", "vakan", "personel", "وظائف", "عمل", "توظيف", "فرص", "ваканси"],
            "sales_team": ["sales", "satis", "satış", "contact", "reach", "ekip", "team", "fiyat", "teklif", "مبيعات", "продаж"],
            "business_clients": ["business", "enterprise", "corporate", "client", "kurumsal", "musteri", "müşteri", "cozum", "çözüm", "عملاء", "بيزنس"],
            "employees": ["employee", "worker", "personnel", "how many", "çalışan", "calisan", "sayısı", "sayisi", "موظف", "كم عدد", "сотрудник"],
            "greeting": ["hello", "hi", "merhaba", "selam", "مرحبا", "مرحبًا", "أهلاً", "привет", "добрый"]
        }
        
        topic_keywords["hr"] = topic_keywords["career_info"]
        topic_keywords["recruitment"] = topic_keywords["career_info"]
        topic_keywords["working_days"] = topic_keywords["working_hours"]

        # Topic grounding
        if intent in topic_keywords:
            if any(kw in normalized_query for kw in topic_keywords[intent]):
                return True
        else:
            # Fallback for RAG matches where intent is unknown/predicted differently
            for kws in topic_keywords.values():
                matched_kw = next((kw for kw in kws if kw in normalized_query), None)
                if matched_kw:
                    if any(kw in answer_lower for kw in kws):
                        return True

        has_identity_in_query = any(w in normalized_query for w in identity_keywords)
        
        # Strict grounding for generic intents
        if intent in ["mission", "vision"]:
            if not has_identity_in_query:
                phrases = ["what is", "tell me", "vizyon", "misyon", "رؤية", "مهمة", "миссия", "видение"]
                if not any(p in normalized_query for p in phrases):
                    return False

        # Identity matching bypass
        if has_identity_in_query:
            return True

        # Token overlap fallback
        if not query_words:
            return True
            
        for word in query_words:
            if word in answer_lower:
                return True

        return False

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
        # Lowered threshold to 0.12 to improve recall for valid but terse queries
        if best["score"] < 0.12:
            return None, None

        if best.get("lang") != language:
            return None, None

        return best["answer"], best.get("title")

    def handle_chat(self, message: str, selected_lang: str | None = None, session_id: str | None = None) -> dict[str, Any]:
        """Main chat orchestration logic."""
        message = message or ""
        normalized = self._normalize(message)
        
        # Detect language early for suggestion bypass and bad word check
        if not selected_lang or selected_lang not in language_service.LOCALES:
            selected_lang = language_service.detect_language(message)

        # 0. Profanity Check (Language-Aware)
        if bad_word_service.contains_bad_word(message, selected_lang):
            ban_replies = {
                "en": "⚠️ Your message contains inappropriate language. Chat has been disabled for 5 minutes.",
                "tr": "⚠️ Mesajınız uygunsuz ifadeler içeriyor. Sohbet 5 dakika süreyle devre dışı bırakıldı.",
                "ar": "⚠️ رسالتك تحتوي على لغة غير لائقة. تم تعطيل المحادثة لمدة 5 دقائق.",
                "ru": "⚠️ Ваше сообщение содержит ненормативную лексику. Чат заблокирован на 5 минут.",
            }
            reply = ban_replies.get(selected_lang, ban_replies["en"])
            logger.warning("Bad word detected in message (lang=%s); banning user.", selected_lang)
            return {
                "reply": reply,
                "language": selected_lang,
                "is_banned": True
            }

        # Bypass grounding for exact suggestions
        is_suggestion = False
        all_suggestions = []
        for l in self.suggestions_by_lang.values():
            all_suggestions.extend([s.lower() for s in l])
        if message.lower() in all_suggestions:
            is_suggestion = True

        # 1. Memory Context (Feature 1)
        history = []
        if session_id:
            history = memory_store.get_history(session_id)
        
        context_query = message
        if history:
            last_user_turns = [t["content"] for t in history if t["role"] == "user"]
            if last_user_turns:
                context_query = f"{last_user_turns[-1]} {message}"

        detected_lang = language_service.detect_language(message)
        is_mismatch = (detected_lang != selected_lang)
        lang_warning = language_service.get_language_warning(detected_lang, selected_lang) if is_mismatch else None
        
        suggestions = self.suggestions_by_lang.get(selected_lang, self.suggestions_by_lang["en"])

        def build_result(reply: str = "", intent: str | None = None, 
                         clarification: list[str] | None = None) -> dict[str, Any]:
            resource_map = self.intent_resource_paths.get(selected_lang, self.intent_resource_paths["default"])
            path = resource_map.get(intent) if intent else None
            
            url = None
            if path:
                url = path if path.startswith("http") else f"{self.base_url}/{selected_lang}/{path}"

            if session_id and reply:
                memory_store.add_turn(session_id, "user", message)
                memory_store.add_turn(session_id, "assistant", reply)

            return {
                "reply": reply,
                "intent": intent,
                "language": selected_lang,
                "suggestions": suggestions,
                "language_warning": lang_warning,
                "is_mismatch": is_mismatch,
                "suggested_language": detected_lang,
                "resource_url": url,
                "session_id": session_id,
                "clarification_options": clarification,
                "is_banned": False
            }

        # 2. Rule-based check for identity queries
        if "toros yazilim" in normalized or "toros yazılım" in normalized:
            return build_result(self._answer_about_toros(selected_lang), intent="company_overview")

        # 3. Intent Engine + Clarification (Feature 2)
        top_intents = predict_top_k(context_query, k=3)
        intent_label, confidence = top_intents[0]

        if confidence < 0.40 and len(top_intents) > 1:
            if confidence > 0.15:
                clarification_labels = [label for label, score in top_intents if score > 0.10]
                if len(clarification_labels) > 1:
                    prompt = {
                        "en": "I'm not sure if you meant one of these. Could you clarify?",
                        "tr": "Tam olarak neyi kastettiğinizden emin olamadım. Şunlardan birini mi demek istediniz?",
                        "ru": "Я не совсем уверен, что вы имели в виду. Не могли бы вы уточнить?",
                        "ar": "لست متأكداً مما تقصده تماماً. هل تقصد أحد هذه الاختيارات؟"
                    }.get(selected_lang, "Could you clarify?")
                    return build_result(prompt, clarification=clarification_labels)

        # 4. Hybrid Slot Extraction (Feature 3)
        extracted_slot = extract_slot(intent_label, context_query)
        final_intent = extracted_slot if extracted_slot else intent_label

        # 5. Knowledge Base Lookup
        kb_answer = None
        kb_items = self.knowledge_base.get(selected_lang, [])
        for item in kb_items:
            if item.get("title") == final_intent:
                kb_answer = item["answer"]
                break
        
        if not kb_answer:
            kb_answer, _ = self._answer_from_knowledge_base(context_query, selected_lang)

        # 6. Answer Grounding Check (Feature 4)
        if kb_answer:
            if is_suggestion or self._is_answer_grounded(message, kb_answer, intent=final_intent):
                return build_result(kb_answer, intent=final_intent)

        # 7. Final Fallback
        reply_text = self.fallback_messages.get(selected_lang, self.fallback_messages["en"])
        log_failed_example(FailedExample(
            text=message,
            predicted_intent=str(final_intent),
            language=selected_lang,
            model_confidence=float(confidence)
        ))

        return build_result(reply_text)

chat_service = ChatService()
