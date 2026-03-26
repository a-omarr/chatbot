from __future__ import annotations

import re
import unicodedata

def _normalize(text: str) -> str:
    """Lowercase and remove punctuation for robust keyword matching."""
    text = unicodedata.normalize("NFKD", text.lower())
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())

# Mapping of broad intents to fine-grained slots (which are also standalone intents)
SLOT_MAP: dict[str, dict[str, list[str]]] = {
    "company_overview": {
        "founding_year": ["founded", "established", "when", "since", "year", "2008", "kurulus", "ne zaman", "kuruldu", "hangi yil"],
        "location": ["where", "located", "city", "mersin", "address", "office", "nerede", "konum", "adres", "ofis"],
        "mission": ["mission", "goal", "objective", "misyon", "amac", "hedef"],
        "vision": ["vision", "future", "target", "vizyon", "gelecek", "hedef"]
    },
    "contact_info": {
        "phone_number": ["phone", "telephone", "call", "number", "contact number", "telefon", "numara", "nolu"],
        "location": ["where", "located", "city", "mersin", "address", "office", "nerede", "konum", "adres", "ofis"]
    },
    "services": {
        "custom_software": ["custom", "software", "development", "build", "app", "ozel", "yazilim", "gelistirme", "kodlama"],
        "it_consultancy": ["consultancy", "advice", "audit", "optimization", "danismanlik", "analiz", "optimizasyon"]
    }
}

def extract_slot(intent: str, text: str) -> str | None:
    """Extract a fine-grained slot from text if it belongs to a known broad intent."""
    if intent not in SLOT_MAP:
        return None
    
    normalized_text = f" {_normalize(text)} "
    slots = SLOT_MAP[intent]
    
    for slot_name, keywords in slots.items():
        for kw in keywords:
            # Check for whole-word keyword match
            if f" {_normalize(kw)} " in normalized_text:
                return slot_name
                
    return None
