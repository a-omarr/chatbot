from __future__ import annotations

import re
from typing import Final

from app.core.loader import get_config

config = get_config()

class LanguageService:
    """Service for language detection and localized warnings."""

    LOCALES: Final = {"en", "tr", "ar", "ru"}
    
    def __init__(self):
        self.msg_templates = {
            "en": "It looks like you're typing in {lang}. Would you like to switch?",
            "tr": "{lang} dilinde yazıyor gibisiniz. Geçmek ister misiniz?",
            "ar": "يبدو أنك تكتب بـ{lang}. هل تريد التبديل؟",
            "ru": "Похоже, вы печатаете на {lang}. Хотите переключиться?",
        }
        
        self.language_names = {
            "en": {"en": "English", "tr": "İngilizce", "ar": "الإنجليزية", "ru": "Английский"},
            "tr": {"en": "Turkish", "tr": "Türkçe", "ar": "التركية", "ru": "Турецкий"},
            "ar": {"en": "Arabic", "tr": "Arapça", "ar": "العربية", "ru": "Арабский"},
            "ru": {"en": "Russian", "tr": "Rusça", "ar": "الروسية", "ru": "Русский"},
        }

    def detect_language(self, text: str) -> str:
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

    def get_language_warning(self, detected: str, selected: str) -> str | None:
        """Generate a friendly warning if the detected language differs from the selection."""
        if detected == selected or detected not in self.LOCALES or selected not in self.LOCALES:
            return None
        
        lang_name = self.language_names.get(detected, {}).get(selected, detected)
        template = self.msg_templates.get(selected, self.msg_templates["en"])
        return template.format(lang=lang_name)

language_service = LanguageService()
