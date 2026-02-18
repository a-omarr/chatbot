import pytest
from app.ml.intent_classifier import predict_intent
from api.v1.bot import chat, ChatRequest, _detect_language_from_text

@pytest.mark.asyncio
async def test_intent_prediction_scenarios():
    test_cases = [
        # --- English ---
        ("Who is Toros Yazilim?", "company_overview"),
        ("What services do you offer?", "services"),
        ("Tell me about your siber security solutions", "cybersecurity"),
        ("I need a project quote for enterprise software", "contact_info"),
        ("Do you work with the public sector?", "public_sector"),
        ("Are you hiring?", "career_info"),
        ("What is your phone number?", "contact_info"),
        ("Where are you located?", "contact_info"),
        ("I want to buy your products", "contact_info"),
        ("Tell me about Makscyber SIEM", "makscyber_siem"),
        ("What is AuthNAC?", "authnac_info"),
        
        # --- Turkish ---
        ("Toros Yazilim kimdir?", "company_overview"),
        ("Hangi hizmetleri sunuyorsunuz?", "services"),
        ("Siber güvenlik çözümleriniz neler?", "cybersecurity"),
        ("Kurumsal yazılım desteği alabilir miyim?", "business_clients"),
        ("Kamu kurumlarına hizmet veriyor musunuz?", "public_sector"),
        ("İş başvurusu nasıl yaparım?", "career_info"),
        ("Telefon numaranız nedir?", "contact_info"),
        ("Adresiniz neresi?", "contact_info"),
        ("Fiyat teklifi alabilir miyim?", "contact_info"),
        ("Makscyber SIEM nedir?", "makscyber_siem"),

        # --- Arabic ---
        ("من هي توروس يازليم؟", "company_overview"),
        ("ما هي الخدمات التي تقدمونها؟", "services"),
        ("أريد معرفة المزيد عن الأمن السيبراني", "cybersecurity"),
        ("هل تقدمون حلولاً للشركات؟", "business_clients"),
        ("وظائف شاغرة", "career_info"),

        # --- Russian ---
        ("Кто такая Toros Yazilim?", "company_overview"),
        ("Какие услуги вы предлагаете?", "services"),
        ("Расскажите о кибербезопасности", "cybersecurity"),
        ("У вас есть вакансии?", "career_info"),
    ]

    for text, expected in test_cases:
        label, confidence = predict_intent(text)
        assert label == expected, f"Failed for '{text}': expected {expected}, got {label}"
        # Some short queries might have lower confidence but should still be the top prediction
        assert confidence > 0.10, f"Confidence too low for '{text}': {confidence}"

@pytest.mark.asyncio
async def test_language_detection_accuracy():
    """Verify that the improved language detector handles brand names and scripts correctly."""
    test_cases = [
        # The key fix: English sentence containing Turkish brand names should stay English
        ("Who is Toros Yazilim?", "en"),
        ("Tell me about KIYOS product", "en"),
        ("I want to know about MAKSCYBER SIEM", "en"),
        ("Does AuthNAC support LDAP?", "en"),
        
        # Pure Turkish
        ("Merhaba, nasılsınız?", "tr"),
        ("Hangi hizmetleri sunuyorsunuz?", "tr"),
        ("Toros Yazılım hakkında bilgi ver", "tr"), # Turkish char 'ı' helps
        
        # Arabic script
        ("مرحبا", "ar"),
        ("من هي توروس يازليم؟", "ar"),
        
        # Cyrillic script
        ("Привет", "ru"),
        ("Кто такая Toros Yazilim?", "ru"),
        
        # Mixed/Edge cases
        ("Hello!", "en"),
        ("Thanks", "en"),
        ("Ok", "en"),
        ("Toros Yazilim", "en"), # Default to en for pure brand name without tr markers
        
        # Greetings
        ("Merhaba", "tr"),
        ("Hello", "en"),
        ("Hi", "en"),
        ("مرحبا", "ar"),
        ("Привет", "ru"),
    ]

    for text, expected in test_cases:
        detected = _detect_language_from_text(text)
        assert detected == expected, f"Detected {detected} for '{text}', expected {expected}"

@pytest.mark.asyncio
async def test_chat_endpoint_responses():
    # Test specific answer content for a few cases
    test_cases = [
        ("en", "What is Makscyber SIEM?", "makscyber_siem", "real-time log analysis"),
        ("tr", "İşe alım yapıyor musunuz?", "career_info", "yetenekli bireyler arıyoruz"),
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
async def test_strict_language_mismatch_suppression():
    """Verify that even a high-confidence greeting is suppressed if the language mismatches."""
    # User sends Turkish greeting while session is English
    test_cases = [
        ("Merhaba", "en"),
        ("merahaba", "en"), # Typo handling
    ]
    for text, lang in test_cases:
        req = ChatRequest(message=text, language=lang)
        resp = await chat(req)
        
        assert resp.is_mismatch is True
        assert resp.suggested_language == "tr"
        assert resp.reply == ""  # STRICTURE: Must be suppressed
        assert resp.language_warning is not None

@pytest.mark.asyncio
async def test_language_mismatch_logic():
    # Detect TR while selecting EN should yield warning but still answer
    # Use clearly Turkish text to ensure detection works
    req = ChatRequest(message="Merhaba, nasılsınız?", language="en")
    resp = await chat(req)
    assert resp.language_warning is not None
    assert "Turkish" in resp.language_warning or "Türkçe" in resp.language_warning
    # Should still provide a real answer (not a blocking error)
    assert "switch to the correct language" not in resp.reply

@pytest.mark.asyncio
async def test_all_ui_suggestions():
    """Verify that every question suggested in Chat.tsx has a valid answer in the KB."""
    suggestions = [
        # Cybersecurity
        "What is Makscyber SIEM?",
        "What does AuthNAC do?",
        "Do you offer identity management solutions?",
        "How can I improve my company’s cybersecurity?",
        "Can I request a demo for your security products?",
        # Business
        "Do you build custom software?",
        "Do you develop enterprise software?",
        "Can you integrate with our existing systems?",
        "Do you provide IT consultancy services?",
        "Can I get a project quote?",
        # Corporate
        "Who is Toros Yazilim?",
        "What services do you offer?",
        "Where is Toros Yazilim located?",
        "Do you work with government institutions?",
        "Are your systems compliant with security standards?",
        # Contact
        "How can I contact you?",
        "How can I contact your sales team?",
        "What is your phone number?",
        "Can I request a demo?",
        # Careers
        "Are you hiring?",
        "Do you offer internships?",
        "How can I apply for a job?",
    ]
    
    for msg in suggestions:
        req = ChatRequest(message=msg, language="en")
        resp = await chat(req)
        assert resp.reply != "", f"Bot provided empty reply for suggestion: '{msg}'"
        assert "You said:" not in resp.reply, f"Bot echoed instead of answering suggestion: '{msg}'"
        assert len(resp.reply) > 20, f"Reply too short for suggestion: '{msg}'"

@pytest.mark.asyncio
async def test_fallback_behavior():
    # With RAG enabled, even unusual input should get a relevant KB answer
    # instead of the old "You said: ..." echo.
    msg = "where is the company located?"
    req = ChatRequest(message=msg, language="en")
    resp = await chat(req)
    # Should NOT be an echo
    assert "You said:" not in resp.reply
    # Should contain some actual info (address, phone, etc.)
    assert len(resp.reply) > 20
