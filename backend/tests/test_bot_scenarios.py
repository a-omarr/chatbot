import pytest
from backend.app.ml.intent_classifier import predict_intent
from backend.api.v1.bot import chat, ChatRequest

@pytest.mark.asyncio
async def test_intent_prediction_scenarios():
    test_cases = [
        # --- English ---
        ("Who is Toros Yazilim?", "company_overview"),
        ("What services do you offer?", "services"),
        ("Tell me about your siber security solutions", "cybersecurity"),
        ("I need a project quote for enterprise software", "business_clients"),
        ("Do you work with the public sector?", "public_sector"),
        ("Are you hiring?", "careers"),
        
        # --- Turkish ---
        ("Toros Yazilim kimdir?", "company_overview"),
        ("Hangi hizmetleri sunuyorsunuz?", "services"),
        ("Siber güvenlik çözümleriniz neler?", "cybersecurity"),
        ("Kurumsal yazılım desteği alabilir miyim?", "business_clients"),
        ("Kamu kurumlarına hizmet veriyor musunuz?", "public_sector"),
        ("İş başvurusu nasıl yaparım?", "careers"),

        # --- Arabic ---
        ("من هي توروس يازليم؟", "company_overview"),
        ("ما هي الخدمات التي تقدمونها؟", "services"),
        ("أريد معرفة المزيد عن الأمن السيبراني", "cybersecurity"),
        ("هل تقدمون حلولاً للشركات؟", "business_clients"),
        ("وظائف شاغرة", "careers"),

        # --- Russian ---
        ("Кто такая Toros Yazilim?", "company_overview"),
        ("Какие услуги вы предлагаете?", "services"),
        ("Расскажите о кибербезопасности", "cybersecurity"),
        ("У вас есть вакансии?", "careers"),
    ]

    for text, expected in test_cases:
        label, confidence = predict_intent(text)
        assert label == expected, f"Failed for '{text}': expected {expected}, got {label}"
        # Some short queries might have lower confidence but should still be the top prediction
        assert confidence > 0.15, f"Confidence too low for '{text}': {confidence}"

@pytest.mark.asyncio
async def test_chat_endpoint_responses():
    # Test specific answer content for a few cases
    test_cases = [
        ("en", "What is Makscyber SIEM?", "cybersecurity", "MAKSCYBER SIEM"),
        ("tr", "İşe alım yapıyor musunuz?", "careers", "yetenekli çalışma arkadaşları"),
        ("ar", "الأمن السيبراني", "cybersecurity", "الأمن السيبراني"),
    ]

    for lang, msg, intent, snippet in test_cases:
        req = ChatRequest(message=msg, language=lang)
        resp = await chat(req)
        assert snippet.lower() in resp.reply.lower(), f"Snippet '{snippet}' not found in reply for '{msg}'"
        assert resp.language == lang
        assert resp.suggestions is not None
        assert len(resp.suggestions) > 0

@pytest.mark.asyncio
async def test_language_mismatch_logic():
    # Detect TR while selecting EN should yield warning
    req = ChatRequest(message="Merhaba, nasılsınız?", language="en")
    resp = await chat(req)
    assert resp.language_warning is not None
    assert "Turkish" in resp.language_warning or "Türkçe" in resp.language_warning
    # Reply should be fixed error message
    assert "switch to the correct language" in resp.reply

@pytest.mark.asyncio
async def test_fallback_behavior():
    # Nonsense message should fallback to echo in English (default detection)
    msg = "xyz123abc!!!???"
    req = ChatRequest(message=msg, language="en")
    resp = await chat(req)
    assert f"You said: {msg}" in resp.reply
