from __future__ import annotations

"""Simple multilingual intent classifier for Toros Yazilim.

This uses classical ML (TFIDF + LogisticRegression) so you can:
- train on labeled examples
- evaluate with accuracy / confusion matrix
- improve iteratively (active learning)

Supported intents (labels):
- company_overview
- services
- products
- contact
- employees
- other (fallback)

Supported languages: en, tr, ru, ar (mixed text is still handled).
"""

from dataclasses import dataclass
from typing import List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


INTENT_LABELS = [
    "company_overview",
    "services",
    "products",
    "contact",
    "employees",
    "other",
]


@dataclass
class IntentExample:
    text: str
    label: str


def _training_data() -> List[IntentExample]:
    """Hand‑crafted multilingual training set.

    In a real system you would export this to a JSON/CSV dataset and
    grow it over time via active learning.
    """

    examples: List[IntentExample] = []

    # --- English ---
    examples += [
        IntentExample("Who is Toros Yazilim?", "company_overview"),
        IntentExample("What is Toros Yazilim?", "company_overview"),
        IntentExample("Tell me about Toros Yazilim", "company_overview"),
        IntentExample("since when", "company_overview"),
        IntentExample("when was it founded", "company_overview"),
        IntentExample("when did you start", "company_overview"),
        IntentExample("what year was the company established", "company_overview"),
        IntentExample("What does Toros do?", "services"),
        IntentExample("Which services do you offer?", "services"),
        IntentExample("What solutions do you provide for web companies?", "services"),
        IntentExample("Do you build custom software?", "services"),
        IntentExample("I need a specific software solution", "services"),
        IntentExample("Can you develop an app for me?", "services"),
        IntentExample("What products does Toros have?", "products"),
        IntentExample("Tell me about KIYOS", "products"),
        IntentExample("What is AuthNAC?", "products"),
        IntentExample("Details about MAKSCYBER SIEM", "products"),
        IntentExample("What is ARI KONAKLAMA?", "products"),
        IntentExample("Do you have identity management solutions?", "products"),
        IntentExample("Tell me about KIYOS and other products", "products"),
        IntentExample("What R&D projects do you have?", "products"),
        IntentExample("What is your phone number?", "contact"),
        IntentExample("How can I contact you by phone?", "contact"),
        IntentExample("Give me your contact number", "contact"),
        IntentExample("How many employees do you have?", "employees"),
        IntentExample("What is your team size?", "employees"),
        IntentExample("How big is your staff?", "employees"),
        IntentExample("how many employee is there", "employees"),
        IntentExample("number of employees", "employees"),
        IntentExample("do you have many employees", "employees"),
        IntentExample("Hello", "other"),
        IntentExample("Thanks", "other"),
    ]

    # --- Turkish ---
    examples += [
        IntentExample("Toros Yazilim kimdir?", "company_overview"),
        IntentExample("Toros Yazilim hakkında bilgi ver", "company_overview"),
        IntentExample("ne zamandan beri", "company_overview"),
        IntentExample("ne zaman kuruldu", "company_overview"),
        IntentExample("hangi yıl kuruldu", "company_overview"),
        IntentExample("Toros Yazilim ne yapıyor?", "services"),
        IntentExample("Hangi hizmetleri sunuyorsunuz?", "services"),
        IntentExample("Hangi çözümleri sağlıyorsunuz?", "services"),
        IntentExample("Ürünleriniz neler?", "products"),
        IntentExample("KIYOS nedir?", "products"),
        IntentExample("AuthNAC hakkında bilgi ver", "products"),
        IntentExample("ARI KONAKLAMA sistemi nasıl çalışır?", "products"),
        IntentExample("Siber güvenlik ürünleriniz var mı?", "products"),
        IntentExample("KIYOS ve diğer ürünlerden bahseder misiniz?", "products"),
        IntentExample("Telefon numaranız nedir?", "contact"),
        IntentExample("Sizi hangi telefondan arayabilirim?", "contact"),
        IntentExample("Kaç çalışanınız var?", "employees"),
        IntentExample("Ekip büyüklüğünüz nedir?", "employees"),
        IntentExample("merhaba", "other"),
    ]

    # --- Russian ---
    examples += [
        IntentExample("Кто такая Toros Yazilim?", "company_overview"),
        IntentExample("Расскажите о компании Toros Yazilim", "company_overview"),
        IntentExample("Чем занимается Toros Yazilim?", "services"),
        IntentExample("Какие услуги вы предоставляете?", "services"),
        IntentExample("Какие у вас продукты и проекты R&D?", "products"),
        IntentExample("Какой у вас номер телефона?", "contact"),
        IntentExample("Как с вами связаться по телефону?", "contact"),
        IntentExample("Сколько у вас сотрудников?", "employees"),
        IntentExample("Какой размер вашей команды?", "employees"),
        IntentExample("привет", "other"),
    ]

    # --- Arabic ---
    examples += [
        IntentExample("من هي توروس يازليم؟", "company_overview"),
        IntentExample("أخبرني عن شركة توروس يازليم", "company_overview"),
        IntentExample("ما هي الخدمات التي تقدمها توروس يازليم؟", "services"),
        IntentExample("ما هي الحلول التي توفرونها؟", "services"),
        IntentExample("ما هي منتجات توروس يازليم؟", "products"),
        IntentExample("ما هو رقم هاتفكم؟", "contact"),
        IntentExample("كيف يمكنني الاتصال بكم هاتفيًا؟", "contact"),
        IntentExample("كم عدد الموظفين لديكم؟", "employees"),
        IntentExample("ما هو حجم فريقكم؟", "employees"),
        IntentExample("مرحبا", "other"),
    ]

    return examples


def build_pipeline() -> Pipeline:
    """Create a TF‑IDF + LogisticRegression pipeline.

    We use character n‑grams so that it works reasonably across different
    alphabets (Latin, Cyrillic, Arabic) without language‑specific tokenizers.
    """

    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=1,
    )
    clf = LogisticRegression(max_iter=200, multi_class="auto")
    return Pipeline([("vec", vectorizer), ("clf", clf)])


_MODEL: Pipeline | None = None


def train_model() -> Pipeline:
    global _MODEL

    examples = _training_data()
    X = [ex.text for ex in examples]
    y = [ex.label for ex in examples]

    model = build_pipeline()
    model.fit(X, y)

    _MODEL = model
    return model


def get_model() -> Pipeline:
    global _MODEL
    if _MODEL is None:
        _MODEL = train_model()
    return _MODEL


def predict_intent(text: str) -> Tuple[str, float]:
    """Predict intent label and confidence for a given user message."""

    model = get_model()
    proba = model.predict_proba([text])[0]
    label_idx = proba.argmax()
    return model.classes_[label_idx], float(proba[label_idx])


def debug_intent(text: str) -> None:
    """Print model prediction and probabilities (for offline debugging)."""

    model = get_model()
    proba = model.predict_proba([text])[0]
    for label, p in zip(model.classes_, proba):
        print(f"{label:18s}: {p:.3f}")
