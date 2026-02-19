import pytest
from app.ml.intent_classifier import predict_intent

@pytest.mark.parametrize("text,expected_intent", [
    ("What are your services?", "services"),
    ("Who is Toros Yazilim?", "company_overview"),
    ("How many people work there?", "employees"),
    ("İş başvurusu nasıl yapılır?", "career_info"),
    ("Size nasıl ulaşabilirim?", "contact_info"),
    ("Merhaba", "greeting"),
    ("What are KIYOS features?", "kiyos_features"),
    ("KIYOS özellikleri nelerdir?", "kiyos_features"),
    ("كيف يمكنني الاتصال بكم؟", "contact_info"),
    ("Кто такая Toros Yazilim?", "company_overview"),
    ("Arı konaklama nedir?", "ari_konaklama"),
])
def test_core_intents(text, expected_intent):
    intent, confidence = predict_intent(text)
    assert intent == expected_intent
    assert confidence > 0.10
