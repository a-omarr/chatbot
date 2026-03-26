from __future__ import annotations

import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.chat_service import chat_service
from app.ml.intent_engine import train_model

def test_enhancements():
    # 0. Train model so it has the new intents
    train_model()
    
    print("\n--- TEST: Richer KB & Slot Extraction ---")
    res = chat_service.handle_chat("When was it founded?", selected_lang="en")
    print(f"Query: 'When was it founded?' -> Intent: {res.get('intent', '?')}, Reply: {res['reply'][:50]}...")
    assert "2008" in res["reply"], "Should return the founding year specific answer"

    res = chat_service.handle_chat("What are your working hours?", selected_lang="en")
    print(f"Query: 'Working hours?' -> Reply: {res['reply'][:50]}...")
    assert "09:00" in res["reply"], "Should return working hours"

    print("\n--- TEST: Conversational Memory (Feature 1) ---")
    session_id = "test_user_123"
    # First turn: Ask about Toros
    chat_service.handle_chat("Tell me about Toros Yazilim", selected_lang="en", session_id=session_id)
    # Second turn: Follow up with "Where is it?"
    res = chat_service.handle_chat("Where is it?", selected_lang="en", session_id=session_id)
    print(f"Follow-up: 'Where is it?' -> Intent: {res.get('intent', '?')}, Reply: {res['reply'][:50]}...")
    assert "Mersin University" in res["reply"], "Should understand 'it' refers to Toros and return location"

    print("\n--- TEST: Confidence-Aware Clarification (Feature 2) ---")
    # Ambiguous query (depends on how much training data we have)
    res = chat_service.handle_chat("Tell me more", selected_lang="en")
    if res.get("clarification_options"):
        print(f"Ambiguous: 'Tell me more' -> Clarification Options: {res['clarification_options']}")
    else:
        print(f"Ambiguous: 'Tell me more' -> Reply: {res['reply'][:50]}...")

    print("\n--- TEST: Answer Grounding & Out-of-Scope (Feature 4) ---")
    # 1. Nonsense Mission
    res = chat_service.handle_chat("I am on a mission to eat pizza", selected_lang="en")
    print(f"Query: 'I am on a mission...' -> Reply: {res['reply'][:50]}...")
    # Should NOT be mission because query doesn't mention Toros/satisfaction
    assert (res.get("intent") or "") != "mission", "Should not match mission for pizza"

    # 4. Suggestion Grounding Bypass (User reported)
    # Even if this isn't a pre-defined suggestion in config.json, 
    # we added keywords like 'quote' and 'demo' to the whitelist.
    fallback_en = chat_service.fallback_messages["en"]
    res = chat_service.handle_chat("Can I get a project quote?", selected_lang="en")
    print(f"Query: 'project quote' -> Intent: {res['intent']}, Reply: {res['reply'][:50]}...")
    assert res["reply"] != fallback_en, "Should NOT fail grounding for a quote request"

    print("\n--- TEST: Language-Aware Profanity (Bug Fix) ---")
    # 1. IT consultancy (EN) - should be safe
    res = chat_service.handle_chat("Do you provide IT consultancy services?", selected_lang="en")
    print(f"Query: 'IT consultancy' -> Is Banned: {res.get('is_banned')}")
    assert not res.get("is_banned"), "IT consultancy should be safe in English"

    # 2. 'am' (EN) - should be safe
    res = chat_service.handle_chat("I am interested in your products", selected_lang="en")
    print(f"Query: 'I am interested...' -> Is Banned: {res.get('is_banned')}")
    assert not res.get("is_banned"), "'am' should be safe in English"

    # 3. 'am' (TR) - should be banned
    # Using 'am' in a Turkish context
    res = chat_service.handle_chat("am", selected_lang="tr")
    print(f"Query: 'am' (TR) -> Is Banned: {res.get('is_banned')}")
    assert res.get("is_banned"), "'am' should be banned in Turkish context"

    print("\nALL ENHANCEMENT TESTS PASSED!")

if __name__ == "__main__":
    test_enhancements()
