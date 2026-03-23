
import sys
import os
import asyncio

# Add backend to path so we can import modules
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.ml.intent_engine import train_model, predict_intent
from api.v1.schemas import ChatRequest
from api.v1.chat_router import chat

async def verify_bot():
    print("--- 1. Training Model ---")
    model = train_model()
    print("Model trained successfully.")

    print("\n--- 2. Testing Intent Prediction ---")
    test_cases = [
        ("Tell me about Toros Yazilim", "company_overview"),
        ("What is KIYOS?", "products"),
        ("Need to contact you", "contact"),
        ("KIYOS nedir?", "products"), # TR
        ("toros yazilim kimdir", "company_overview"), # TR
        ("authnac details", "products"),
        ("how many employee is there", "employees"),
        ("number of employees", "employees"),
        ("Does KIYOS support LDAP?", "products"), # New detailed query
        ("Universal Directory features", "products"), # New detailed query
        ("What custom software do you build?", "services"), # New detailed query
    ]

    for text, expected in test_cases:
        label, conf = predict_intent(text)
        print(f"Input: '{text}' -> Predicted: {label} ({conf:.2f}) | Expected: {expected}")
        # Note: minimal training data might lead to some noise, but we check for general behavior

    print("\n--- 3. Testing Chat Endpoint Logic ---")
    # Test English Product Query
    req_en = ChatRequest(message="Tell me about KIYOS", language="en")
    resp_en = await chat(req_en)
    print(f"EN Query 'Tell me about KIYOS':\nReply: {resp_en.reply[:100]}...")
    
    if resp_en.suggestions and len(resp_en.suggestions) == 5:
        print(f"✅ Suggestions count is 5: {resp_en.suggestions}")
    else:
        print(f"❌ Suggestions count mismatch: {len(resp_en.suggestions) if resp_en.suggestions else 0}")

    # Test TR Company Query
    req_tr = ChatRequest(message="Toros Yazilim kimdir?", language="tr")
    resp_tr = await chat(req_tr)
    print(f"TR Query 'Toros Yazilim kimdir?':\nReply: {resp_tr.reply[:100]}...")

    # Test Fuzzy Match Fallback
    # "telefon" is a keyword. "telefoon" is a typo.
    req_fuzzy = ChatRequest(message="telefoon numarasi", language="tr")
    resp_fuzzy = await chat(req_fuzzy)
    print(f"Fuzzy Query 'telefoon numarasi':\nReply: {resp_fuzzy.reply[:100]}...")

if __name__ == "__main__":
    asyncio.run(verify_bot())
