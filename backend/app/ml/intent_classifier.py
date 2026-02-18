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
    "contact_info",
    "employees",
    "cybersecurity",
    "business_clients",
    "public_sector",
    "career_info",
    "greeting",
    "makscyber_siem",
    "authnac_info",
    "identity_management",
    "custom_software",
    "it_consultancy",
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
        IntentExample("history of the company", "company_overview"),
        IntentExample("about us", "company_overview"),
        IntentExample("What does Toros do?", "services"),
        IntentExample("Which services do you offer?", "services"),
        IntentExample("What solutions do you provide for web companies?", "services"),
        IntentExample("Do you build custom software?", "services"),
        IntentExample("I need a specific software solution", "services"),
        IntentExample("Can you develop an app for me?", "services"),
        IntentExample("software development services", "services"),
        IntentExample("application development", "services"),
        IntentExample("What products does Toros have?", "products"),
        IntentExample("Tell me about KIYOS", "products"),
        IntentExample("What is AuthNAC?", "products"),
        IntentExample("Details about MAKSCYBER SIEM", "products"),
        IntentExample("What is ARI KONAKLAMA?", "products"),
        IntentExample("Do you have identity management solutions?", "products"),
        IntentExample("Tell me about KIYOS and other products", "products"),
        IntentExample("What R&D projects do you have?", "products"),
        IntentExample("list of your software products", "products"),
        IntentExample("identity solution", "products"),
        IntentExample("How can I contact you?", "contact_info"),
        IntentExample("contact details", "contact_info"),
        IntentExample("What is your phone number?", "contact_info"),
        IntentExample("call you", "contact_info"),
        IntentExample("telephone", "contact_info"),
        IntentExample("Give me your contact number", "contact_info"),
        IntentExample("Where is Toros Yazilim located?", "contact_info"),
        IntentExample("office location", "contact_info"),
        IntentExample("address", "contact_info"),
        IntentExample("where are you", "contact_info"),
        IntentExample("how can I contact your sales team?", "contact_info"),
        IntentExample("request a demo", "contact_info"),
        IntentExample("demo", "contact_info"),
        IntentExample("buy", "contact_info"),
        IntentExample("quote", "contact_info"),
        IntentExample("I need a project quote for enterprise software", "contact_info"),
        IntentExample("pricing information", "contact_info"),
        IntentExample("contact form", "contact_info"),
        IntentExample("reach out to you", "contact_info"),
        IntentExample("What is Makscyber SIEM?", "makscyber_siem"),
        IntentExample("tell me about SIEM", "makscyber_siem"),
        IntentExample("log analysis tool", "makscyber_siem"),
        IntentExample("What does AuthNAC do?", "authnac_info"),
        IntentExample("secure authentication", "authnac_info"),
        IntentExample("network access control", "authnac_info"),
        IntentExample("Tell me about your siber security solutions", "cybersecurity"),
        IntentExample("cybersecurity", "cybersecurity"),
        IntentExample("network security", "cybersecurity"),
        IntentExample("Do you offer identity management solutions?", "identity_management"),
        IntentExample("tell me about KIYOS", "identity_management"),
        IntentExample("SSO and MFA", "identity_management"),
        IntentExample("Are you hiring?", "career_info"),
        IntentExample("how to apply for a job", "career_info"),
        IntentExample("career opportunities", "career_info"),
        IntentExample("Do you offer internships?", "career_info"),
        IntentExample("internship program", "career_info"),
        IntentExample("student intern", "career_info"),
        IntentExample("human resources", "career_info"),
        IntentExample("send CV", "career_info"),
        IntentExample("join the team", "career_info"),
        IntentExample("Do you build custom software?", "custom_software"),
        IntentExample("develop an app", "custom_software"),
        IntentExample("enterprise software development", "custom_software"),
        IntentExample("Do you provide IT consultancy services?", "it_consultancy"),
        IntentExample("technology advisor", "it_consultancy"),
        IntentExample("Do you work with government institutions?", "public_sector"),
        IntentExample("Do you work with the public sector?", "public_sector"),
        IntentExample("government clients", "public_sector"),
        IntentExample("Are your systems compliant with security standards?", "public_sector"),
        IntentExample("government work", "public_sector"),
        IntentExample("municipalities", "public_sector"),
        IntentExample("national security standards", "public_sector"),
        IntentExample("Do you develop enterprise software?", "business_clients"),
        IntentExample("Can you integrate with our existing systems?", "business_clients"),
        IntentExample("corporate solutions", "business_clients"),
        IntentExample("How many employees do you have?", "employees"),
        IntentExample("team size", "employees"),
        IntentExample("Hello", "greeting"),
        IntentExample("Thanks", "other"),
    ]

    # --- Turkish ---
    examples += [
        IntentExample("Toros Yazilim kimdir?", "company_overview"),
        IntentExample("Hangi hizmetleri sunuyorsunuz?", "services"),
        IntentExample("telefon numaranız nedir", "contact_info"),
        IntentExample("size nasıl ulaşabilirim", "contact_info"),
        IntentExample("adresiniz neresi", "contact_info"),
        IntentExample("konum bilgisi", "contact_info"),
        IntentExample("satış ekibiyle görüşmek istiyorum", "contact_info"),
        IntentExample("fiyat teklifi", "contact_info"),
        IntentExample("demo talep et", "contact_info"),
        IntentExample("iletişim formu", "contact_info"),
        IntentExample("numaranız var mı", "contact_info"),
        IntentExample("Makscyber SIEM nedir?", "makscyber_siem"),
        IntentExample("log analizi", "makscyber_siem"),
        IntentExample("AuthNAC ne işe yarar?", "authnac_info"),
        IntentExample("ağ erişim kontrolü", "authnac_info"),
        IntentExample("Siber güvenlik çözümleriniz neler?", "cybersecurity"),
        IntentExample("siber güvenlik", "cybersecurity"),
        IntentExample("KIYOS kimlik yönetimi", "identity_management"),
        IntentExample("SSO ve MFA çözümleri", "identity_management"),
        IntentExample("İşe alım yapıyor musunuz?", "career_info"),
        IntentExample("nasıl iş başvurusu yaparım", "career_info"),
        IntentExample("Staj imkanı sunuyor musunuz?", "career_info"),
        IntentExample("staj başvurusu", "career_info"),
        IntentExample("iş ilanları", "career_info"),
        IntentExample("CV gönder", "career_info"),
        IntentExample("özel yazılım geliştirme", "custom_software"),
        IntentExample("BT danışmanlık", "it_consultancy"),
        IntentExample("BT danışmanlık hizmeti veriyor musunuz?", "it_consultancy"),
        IntentExample("Merhaba", "greeting"),
        IntentExample("Selam", "greeting"),
        IntentExample("merhaba", "other"),
    ]

    # --- Russian ---
    examples += [
        IntentExample("Кто такая Toros Yazilim?", "company_overview"),
        IntentExample("Расскажите о компании Toros Yazilim", "company_overview"),
        IntentExample("Чем занимается Toros Yazilim?", "services"),
        IntentExample("Какие услуги вы предоставляете?", "services"),
        IntentExample("Какие у вас продукты и проекты R&D?", "products"),
        IntentExample("Какой у вас номер телефона?", "contact_info"),
        IntentExample("Как с вами связаться по телефону?", "contact_info"),
        IntentExample("где вы находитесь", "contact_info"),
        IntentExample("адрес офиса", "contact_info"),
        IntentExample("запросить демо", "contact_info"),
        IntentExample("Сколько у вас сотрудников?", "employees"),
        IntentExample("Какой размер вашей команды?", "employees"),
        IntentExample("Что такое Makscyber SIEM?", "makscyber_siem"),
        IntentExample("Как работает AuthNAC?", "authnac_info"),
        IntentExample("У вас есть решения для управления идентификацией?", "identity_management"),
        IntentExample("Как улучшить кибербезопасность компании?", "cybersecurity"),
        IntentExample("Вы разрабатываете корпоративное ПО?", "business_clients"),
        IntentExample("У вас есть вакансии?", "career_info"),
        IntentExample("стажировка", "career_info"),
        IntentExample("работа у вас", "career_info"),
        IntentExample("Привет", "greeting"),
        IntentExample("Здравствуйте", "greeting"),
        IntentExample("Добрый день", "greeting"),
        IntentExample("привет", "other"),
    ]

    # --- Arabic ---
    examples += [
        IntentExample("من هي توروس يازليم؟", "company_overview"),
        IntentExample("أخبرني عن شركة توروس يازليم", "company_overview"),
        IntentExample("ما هي الخدمات التي تقدمها توروس يازليم؟", "services"),
        IntentExample("ما هي الحلول التي توفرونها؟", "services"),
        IntentExample("ما هي منتجات توروس يازليم؟", "products"),
        IntentExample("ما هو رقم هاتفكم؟", "contact_info"),
        IntentExample("كيف يمكنني الاتصال بكم هاتفيًا؟", "contact_info"),
        IntentExample("أين يقع مكتبكم؟", "contact_info"),
        IntentExample("عنوان الشركة", "contact_info"),
        IntentExample("طلب عرض تجريبي", "contact_info"),
        IntentExample("كم عدد الموظفين لديكم؟", "employees"),
        IntentExample("ما هو حجم فريقكم؟", "employees"),
        IntentExample("ما هو Makscyber SIEM؟", "makscyber_siem"),
        IntentExample("ماذا يفعل AuthNAC؟", "authnac_info"),
        IntentExample("هل تقدمون حلول إدارة الهوية؟", "identity_management"),
        IntentExample("كيف يمكنني تحسين الأمن السيبراني لشركتي؟", "cybersecurity"),
        IntentExample("هل تقدمون حلولاً للشركات؟", "business_clients"),
        IntentExample("هل تطورون برمجيات للمؤسسات؟", "business_clients"),
        IntentExample("وظائف شاغرة", "career_info"),
        IntentExample("فرص تدريب", "career_info"),
        IntentExample("كيف يمكنني التقدم لوظيفة؟", "career_info"),
        IntentExample("مرحبا", "greeting"),
        IntentExample("السلام عليكم", "greeting"),
        IntentExample("أهلا", "greeting"),
        IntentExample("صباح الخير", "greeting"),
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
