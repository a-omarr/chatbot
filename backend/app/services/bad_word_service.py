from __future__ import annotations

"""Bad word detection service.

Loads a multilingual bad-words knowledge base from JSON and exposes a fast
substring matcher that works across EN, TR, AR, and RU.
"""

import json
import logging
import re
import unicodedata
from pathlib import Path

logger = logging.getLogger(__name__)

# Path to the knowledge base (relative to this file)
_DATA_PATH = Path(__file__).parent.parent / "data" / "bad_words.json"


def _normalize(text: str) -> str:
    """Lowercase, strip diacritics, and remove all non-alphanumeric chars."""
    # Unicode normalization to separate base letters from diacritics
    text = unicodedata.normalize("NFKD", text.lower())
    # Keep letters (including Arabic / Cyrillic) and digits; strip the rest
    text = re.sub(r"[\s\-_'.,:;!?\"()\\/*]+", " ", text)
    return text.strip()


class BadWordService:
    """Singleton service that checks messages for profanity with language awareness."""

    def __init__(self) -> None:
        # Dictionary of normalized words per language: {lang_code: set(words)}
        self._banned_by_lang: dict[str, set[str]] = {}
        self._common: set[str] = set()
        self._load()

    def _load(self) -> None:
        try:
            raw_data: dict[str, list[str]] = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
            
            # Load common words
            common_raw = raw_data.get("common", [])
            self._common = {_normalize(w) for w in common_raw}
            
            # Load language-specific words
            for lang_code, words in raw_data.items():
                if lang_code == "common" or lang_code.startswith("_"):
                    continue
                self._banned_by_lang[lang_code] = {_normalize(w) for w in words}
                
            logger.info("BadWordService: loaded %d common and %d language-specific categories", 
                        len(self._common), len(self._banned_by_lang))
        except Exception:
            logger.exception("BadWordService: failed to load bad_words.json")

    def contains_bad_word(self, text: str, lang: str | None = None) -> bool:
        """Return True if *text* contains any banned phrase as a whole word.
        Only checks words in the 'common' list and the provided 'lang' list.
        """
        normalized = _normalize(text)
        padded_text = f" {normalized} "
        
        # 1. Check common bad words (always)
        for phrase in self._common:
            if f" {phrase} " in padded_text:
                return True
                
        # 2. Check language-specific bad words
        if lang and lang in self._banned_by_lang:
            for phrase in self._banned_by_lang[lang]:
                if f" {phrase} " in padded_text:
                    return True
                    
        return False


# Application-level singleton
bad_word_service = BadWordService()
