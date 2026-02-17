from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any

from app.ml.intent_classifier import predict_intent


class ChatRequest(BaseModel):
    """Incoming chat payload from the frontend."""

    message: str
    # Optional language hint coming from the UI combobox: "en", "tr", "ar", "ru".
    language: str | None = None


class ChatResponse(BaseModel):
    """Chatbot reply structure returned to the frontend."""

    reply: str
    # Optional language code of the reply (e.g. "en", "tr", "ar", "ru").
    language: str | None = None
    # Optional list of suggested follow‑up questions to render as quick‑reply chips.
    suggestions: list[str] | None = None


router = APIRouter()


# Per‑language suggestions so each locale only sees its own examples.
SUGGESTIONS_BY_LANG: dict[str, list[str]] = {
    "en": [
        "Who is Toros Yazilim?",
        "What services do you offer?",
        "What products do you have?",
        "How can I contact you?",
    ],
    "tr": [
        "Toros Yazilim kimdir?",
        "Hangi hizmetleri sunuyorsunuz?",
        "Ürünleriniz neler?",
        "Sizi nasıl iletişime geçebilirim?",
    ],
    "ar": [
        "من هي توروس يازليم؟",
        "ما هي الخدمات التي تقدمها؟",
        "ما هي منتجاتك؟",
        "كيف يمكنني الاتصال بك؟",
    ],
    "ru": [
        "Кто такая Toros Yazilim?",
        "Какие услуги вы предоставляете?",
        "Какие у вас продукты?",
        "Как с вами связаться?",
    ],
}


def _normalize(text: str) -> str:
    """Very small helper to normalise user input for rule‑based matching."""
    return "".join(ch.lower() for ch in text.strip() if ch.isalnum() or ch.isspace())


def _tokenize(text: str) -> list[str]:
    """Simple whitespace tokeniser over the normalised text."""
    return _normalize(text).split()


def _answer_about_toros(language: str) -> str:
    """Return a short description of Toros Yazılım in the given language.

    Content is summarised from https://www.torosyazilim.com/.
    """
    if language == "tr":
        return (
            "Toros Yazılım, web endüstrisiyle ilgili hemen hemen tüm şirketler için "
            "eksiksiz bir hizmet yelpazesi sunan, müşteri odaklı bir yazılım ve "
            "bilişim danışmanlığı şirketidir. Servis entegrasyonları, bilişim ve "
            "danışmanlık hizmetleri, kurumsal firmalara özel yazılım çözümleri sunar. "
            "Teknopark bünyesinde geliştirilen Kimlik Yönetim Sistemi (KIYOS), "
            "ARI Konaklama, MAKSCYBER SIEM ve AuthNAC gibi Ar‑Ge projeleri ile "
            "güvenlik, kimlik yönetimi ve kurumsal ihtiyaçlara yönelik çözümler üretir."
        )
    if language == "ar":
        return (
            "توروس ياز   هي شركة تركية متخصصة في حلول البرمجيات وخدمات تكنولوجيا المعلومات "
            "الاستشارية، تركز على تقديم حلول موجهة للعميل لشركات تعمل في مجال الويب. "
            "تقدم خدمات تكامل الأنظمة، وخدمات التحليل والتخطيط والتحسين والتركيب "
            "والتكامل وحل المشكلات، بالإضافة إلى تطوير حلول برمجية مخصصة للشركات. "
            "من منتجاتها ومشاريعها في واحة التقنية: نظام إدارة الهوية KIYOS، "
            "نظام ARI KONAKLAMA، ومشاريع MAKSCYBER SIEM و AuthNAC للأمن السيبراني "
            "وإدارة الوصول."
        )
    if language == "ru":
        return (
            "Toros Yazılım — турецкая компания в сфере программного обеспечения и "
            "IT‑консалтинга, предлагающая решения, ориентированные на клиента, для "
            "компаний веб‑индустрии. Компания занимается интеграцией сервисов, "
            "оказанием IT‑услуг и консалтинга, а также разработкой индивидуальных "
            "программных решений для корпоративных клиентов. Среди продуктов и "
            "НИОКР‑проектов — система управления идентификацией KIYOS, проект "
            "пчелиного размещения, а также решения MAKSCYBER SIEM и AuthNAC для "
            "кибербезопасности и контроля доступа."
        )

    # Default to English
    return (
        "Toros Yazılım is a customer‑oriented software and IT consulting company in Turkey "
        "that offers a complete range of services for companies in the web industry. "
        "They provide service integrations, IT and consultancy services, and custom "
        "software solutions for corporate clients. Within the technopark they develop "
        "products and R&D projects such as the KIYOS Identity Management System, "
        "BEE Accommodation, and MAKSCYBER SIEM and AuthNAC for cybersecurity and access "
        "control."
    )


from math import sqrt


# Minimal multilingual knowledge base about Toros Yazılım.
KNOWLEDGE_BASE: dict[str, list[dict[str, Any]]] = {
    "en": [
        {
            "title": "company_overview",
            "keywords": ["who", "what", "company", "toros", "yazilim"],
            "answer": _answer_about_toros("en"),
        },
        {
            "title": "services",
            "keywords": ["services", "solutions", "what do you offer", "web industry"],
            "answer": (
                "Toros Yazilim offers customer‑oriented solutions for companies in the web "
                "industry. They provide service integrations, IT and consultancy services "
                "such as analysis, planning, optimisation, installation/integration and "
                "troubleshooting, and also build custom software solutions tailored to the "
                "needs of corporate customers."
            ),
        },
        {
            "title": "products",
            "keywords": ["products", "identity", "kiyos", "bee", "siem", "authnac"],
            "answer": (
                "Within the technopark, Toros Yazilim develops products and R&D projects such "
                "as the KIYOS Identity Management System, BEE Accommodation for beekeeper "
                "placement and tracking, and MAKSCYBER SIEM and AuthNAC for real‑time security "
                "analytics and access control."
            ),
        },
        {
            "title": "contact",
            "keywords": ["phone", "telephone", "call", "phone number", "contact number"],
            "answer": (
                "You can contact Toros Yazilim by phone at 0(324) 404 0 808. "
                "This number is listed on the Contact section of their official website."
            ),
        },
        {
            "title": "employees",
            "keywords": ["how many employees", "staff", "team size"],
            "answer": (
                "The public Toros Yazilim website focuses on the company’s services, products and "
                "R&D projects, but it does not state an exact number of employees. It highlights "
                "their expertise, partnerships and customer‑oriented approach rather than a "
                "specific headcount."
            ),
        },
    ],
    "tr": [
        {
            "title": "company_overview",
            "keywords": ["toros", "yazilim", "kimdir", "hakkında", "şirket"],
            "answer": _answer_about_toros("tr"),
        },
        {
            "title": "services",
            "keywords": ["hizmetler", "çözümler", "neler sunuyorsunuz", "müşteri odaklı"],
            "answer": (
                "Toros Yazılım, web endüstrisiyle ilgili şirketler için müşteri odaklı çözümler "
                "sunar. Birden çok sistem ve uygulamanın entegre edilmesini sağlayan servis "
                "entegrasyonları, bilişim ve danışmanlık hizmetleri (analiz, planlama, "
                "optimizasyon, kurulum/entegrasyon ve sorun giderme) ve kurumsal firmalara özel "
                "yazılım çözümleri geliştirmektedir."
            ),
        },
        {
            "title": "products",
            "keywords": ["ürünler", "kimlik yönetim sistemi", "kiyos", "ari konaklama", "siem", "authnac"],
            "answer": (
                "Teknopark bünyesinde geliştirilen başlıca ürün ve Ar‑Ge projeleri arasında KIYOS "
                "Kimlik Yönetim Sistemi, ARI KONAKLAMA otomasyon sistemi ile MAKSCYBER SIEM ve "
                "AuthNAC gibi siber güvenlik ve erişim kontrolü çözümleri yer almaktadır."
            ),
        },
        {
            "title": "contact",
            "keywords": ["telefon", "telefon numarası", "iletişim", "arama"],
            "answer": (
                "Toros Yazılım’a 0(324) 404 0 808 numaralı telefondan ulaşabilirsiniz. "
                "Bu telefon numarası resmi web sitesindeki iletişim sayfasında yer almaktadır."
            ),
        },
        {
            "title": "employees",
            "keywords": ["kaç çalışan", "kaç kişi", "çalışan sayısı", "ekip büyüklüğü"],
            "answer": (
                "Toros Yazılım’ın herkese açık web sitesi; hizmetler, ürünler ve Ar‑Ge projelerine "
                "odaklanmakta, ancak çalışan sayısını açıkça belirtmemektedir. Şirket, ekip "
                "büyüklüğünden çok uzmanlık, iş ortaklıkları ve müşteri odaklı yaklaşımını "
                "vurgulamaktadır."
            ),
        },
    ],
    "ru": [
        {
            "title": "company_overview",
            "keywords": ["toros", "yazilim", "кто", "компания", "о нас"],
            "answer": _answer_about_toros("ru"),
        },
        {
            "title": "services",
            "keywords": ["услуги", "решения", "что вы предлагаете", "веб индустрии"],
            "answer": (
                "Toros Yazılım предоставляет решения, ориентированные на клиента, для компаний "
                "в веб‑индустрии. Компания выполняет интеграцию сервисов, оказывает IT‑услуги и "
                "консалтинг — анализ, планирование, оптимизацию, установку/интеграцию и "
                "устранение проблем — а также разрабатывает индивидуальные программные решения "
                "для корпоративных клиентов."
            ),
        },
        {
            "title": "products",
            "keywords": ["продукты", "решения", "система управления идентификацией", "kiyos", "siem", "authnac"],
            "answer": (
                "В технопарке Toros Yazılım разрабатывает продукты и НИОКР‑проекты, такие как "
                "система управления идентификацией KIYOS, проект размещения пчеловодов, а также "
                "решения MAKSCYBER SIEM и AuthNAC для кибербезопасности и контроля доступа."
            ),
        },
        {
            "title": "contact",
            "keywords": ["телефон", "номер телефона", "контакт", "позвонить"],
            "answer": (
                "Связаться с Toros Yazilim можно по телефону 0(324) 404 0 808. "
                "Этот номер указан в разделе контактов на официальном сайте компании."
            ),
        },
        {
            "title": "employees",
            "keywords": ["сколько сотрудников", "сколько человек", "число сотрудников", "размер команды"],
            "answer": (
                "Открытый сайт Toros Yazılım подробно рассказывает об услугах, продуктах и "
                "НИОКР‑проектах компании, но не указывает точное количество сотрудников. "
                "Акцент делается на экспертизе, партнерствах и ориентации на клиента, а не на "
                "конкретной численности штата."
            ),
        },
    ],
    "ar": [
        {
            "title": "company_overview",
            "keywords": ["توروس", "يازليم", "من هي", "الشركة"],
            "answer": _answer_about_toros("ar"),
        },
        {
            "title": "services",
            "keywords": ["الخدمات", "الحلول", "ماذا تقدمون", "موجهة للعملاء"],
            "answer": (
                "توروس يازليم تقدم حلولاً موجهة للعملاء للشركات العاملة في مجال الويب. "
                "تقدم خدمات تكامل الأنظمة، وخدمات تكنولوجيا المعلومات والاستشارات مثل "
                "التحليل والتخطيط والتحسين والتركيب/التكامل وحل المشكلات، بالإضافة إلى "
                "تطوير حلول برمجية مخصصة لاحتياجات الشركات."
            ),
        },
        {
            "title": "products",
            "keywords": ["المنتجات", "kiyos", "نظام إدارة الهوية", "ari", "siem", "authnac"],
            "answer": (
                "من بين المنتجات والمشاريع التي تطورها توروس يازليم في واحة التقنية: نظام "
                "إدارة الهوية KIYOS، نظام ARI KONAKLAMA لأتمتة عمليات الإقامة، ومشاريع "
                "MAKSCYBER SIEM و AuthNAC لتحليل سجلات الأمن وإدارة التحكم في الوصول."
            ),
        },
        {
            "title": "contact",
            "keywords": ["الهاتف", "رقم الهاتف", "الاتصال", "رقم الاتصال"],
            "answer": (
                "يمكنك التواصل مع توروس يازليم عبر الهاتف على الرقم 0(324) 404 0 808. "
                "يظهر هذا الرقم في صفحة التواصل على الموقع الرسمي للشركة."
            ),
        },
        {
            "title": "employees",
            "keywords": ["كم عدد الموظفين", "عدد الموظفين", "حجم الفريق", "كم شخص"],
            "answer": (
                "الموقع الرسمي لتوروس يازليم يركز على الخدمات والمنتجات ومشاريع البحث "
                "والتطوير، ولا يذكر عدداً دقيقاً للموظفين. يتم إبراز الخبرة والشراكات "
                "والتركيز على احتياجات العملاء أكثر من التركيز على حجم الفريق."
            ),
        },
    ],
}


def _score_knowledge_item(query_tokens: list[str], item: dict[str, Any]) -> float:
    """Very small similarity score between the user query and a KB item.

    This is intentionally simple (token overlap) to avoid external ML dependencies
    while still behaving like a tiny retrieval model.
    """
    keyword_strings = item.get("keywords", [])
    if not keyword_strings:
        return 0.0

    keywords_tokens: set[str] = set()
    for kw in keyword_strings:
        for tok in _tokenize(kw):
            keywords_tokens.add(tok)

    if not keywords_tokens:
        return 0.0

    query_set = set(query_tokens)
    overlap = len(query_set.intersection(keywords_tokens))
    return overlap / float(len(keywords_tokens))


def _answer_from_knowledge_base(message: str, language: str) -> str | None:
    """Return the best‑matching knowledge‑base answer for the given message.

    This acts as a light‑weight, retrieval‑style 'ML' model that finds which
    Toros Yazılım topic the question is closest to for the selected language.
    """
    kb_items = KNOWLEDGE_BASE.get(language)
    if not kb_items:
        return None

    tokens = _tokenize(message)
    if not tokens:
        return None

    best_score = 0.0
    best_answer: str | None = None
    for item in kb_items:
        score = _score_knowledge_item(tokens, item)
        if score > best_score:
            best_score = score
            best_answer = item["answer"]

    # Require at least a minimal score so we don't answer completely unrelated questions.
    if best_score <= 0.0:
        return None

    return best_answer


def _detect_language_from_text(text: str) -> str:
    """Naive language detection for the Toros Yazılım intent only.

    For real production use you would replace this with an ML model or external
    language‑detection service.
    """
    lowered = text.lower()
    # Heuristics based on common phrases / alphabet
    if any(token in lowered for token in ["kimdir", "yazılım", "yazilim"]):
        return "tr"
    if any(0x600 < ord(ch) < 0x6FF for ch in text):
        # Basic Arabic block check
        return "ar"
    if "кто" in lowered:
        return "ru"
    return "en"


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Simple multilingual rule‑based chatbot endpoint.

    - Suggests sample questions about Toros Yazılım.
    - Detects when the user is asking “Who is Toros Yazılım?” in English, Turkish,
      Arabic or Russian and answers in that language.
    - Falls back to a basic echo‑style response for other queries.
    """
    raw_message = request.message or ""
    normalized = _normalize(raw_message)

    # Decide language: UI hint wins, otherwise detect from text.
    lang_hint = (request.language or "").lower() if request.language else None
    if lang_hint in {"en", "tr", "ar", "ru"}:
        lang = lang_hint
    else:
        lang = _detect_language_from_text(raw_message)

    suggestions = SUGGESTIONS_BY_LANG.get(lang, SUGGESTIONS_BY_LANG["en"])

    # Very small intent detection for "Who is Toros Yazilim?"
    # Latin‑script variants (EN/TR/RU suggestion buttons and typed text)
    if "toros yazilim" in normalized or "toros yazılım" in normalized:
        reply_text = _answer_about_toros(lang)
        return ChatResponse(reply=reply_text, language=lang, suggestions=suggestions)

    # Arabic variant from the Arabic suggestion button / user input.
    if lang == "ar" and ("توروس" in raw_message and "يازليم" in raw_message):
        reply_text = _answer_about_toros("ar")
        return ChatResponse(reply=reply_text, language="ar", suggestions=suggestions)

    # 1) Intent classification using ML model
    intent_label, confidence = predict_intent(raw_message)

    # 2) Try to answer from the structured knowledge base using the intent.
    #    We look for the KB item whose `title` matches the predicted intent.
    kb_items = KNOWLEDGE_BASE.get(lang, [])
    for item in kb_items:
        if item.get("title") == intent_label:
            return ChatResponse(reply=item["answer"], language=lang, suggestions=suggestions)

    # 3) If that fails, fall back to similarity search inside the KB.
    kb_answer = _answer_from_knowledge_base(raw_message, lang)
    if kb_answer:
        return ChatResponse(reply=kb_answer, language=lang, suggestions=suggestions)

    # Fallback behaviour – keep echo‑style reply but still send locale‑specific suggestions.
    reply_text = f"You said: {raw_message}"

    return ChatResponse(reply=reply_text, language=lang, suggestions=suggestions)
