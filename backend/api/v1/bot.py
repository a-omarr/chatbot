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
    # Optional warning when detected language doesn't match selected language
    language_warning: str | None = None


router = APIRouter()


# Per‑language suggestions so each locale only sees its own examples.
SUGGESTIONS_BY_LANG: dict[str, list[str]] = {
    "en": [
        "Who is Toros Yazilim?",
        "Tell me about KIYOS",
        "What services do you offer?",
        "Does KIYOS support LDAP?",
        "How can I contact you?",
    ],
    "tr": [
        "Toros Yazilim kimdir?",
        "KIYOS nedir?",
        "Hizmetleriniz neler?",
        "KIYOS LDAP destekliyor mu?",
        "Size nasıl ulaşabilirim?",
    ],
    "ar": [
        "من هي توروس يازليم؟",
        "أخبرني عن KIYOS",
        "ما هي خدماتكم؟",
        "هل يدعم KIYOS نظام LDAP؟",
        "كيف يمكنني الاتصال بكم؟",
    ],
    "ru": [
        "Кто такая Toros Yazilim?",
        "Расскажите о KIYOS",
        "Какие услуги вы предлагаете?",
        "Поддерживает ли KIYOS LDAP?",
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
        "Toros Yazılım is a customer‑oriented software and IT consulting company founded in 2008 "
        "in Mersin. We offer a complete range of services for companies in the web industry, "
        "including service integrations, IT consultancy, and custom software solutions. "
        "Our mission is to maximize customer satisfaction through high-quality solutions using "
        "up-to-date technology."
    )


from math import sqrt


# Minimal multilingual knowledge base about Toros Yazılım.
KNOWLEDGE_BASE: dict[str, list[dict[str, Any]]] = {
    "en": [
        {
            "title": "employees",
            "keywords": ["how many employees", "staff", "team size", "headcount", "workforce"],
            "answer": (
                "The public sections of our website (including Human Resources and About Us) do not specify "
                "an exact number of employees. Toros Yazilim was founded in 2008 and has grown into a "
                "team of specialized experts working in a technopark environment, but the exact headcount "
                "is not publicly listed."
            ),
        },
        {
            "title": "company_overview",
            "keywords": ["who", "what", "company", "toros", "yazilim", "mission", "vision", "about", "since", "when", "founded", "established", "2008", "year"],
            "answer": (
                "Toros Yazılım was founded in 2008 in Mersin by young entrepreneurs. "
                "**Mission**: To maximize customer satisfaction through high-quality solutions using up-to-date technology. "
                "**Vision**: To become an international brand and one of Turkey’s leading software companies. "
                "**Principles**: Customer Focus, Problem Solving, Teamwork, Openness to Learning."
            ),
        },
        {
            "title": "services",
            "keywords": ["services", "solutions", "consultancy", "integration", "software development", "analysis"],
            "answer": (
                "We provide comprehensive services ensuring high business ethics and after-sales reliability:\n"
                "1. **Service Integrations**: Integrating data from multiple platforms and systems.\n"
                "2. **IT & Consultancy**: Analysis, planning, optimization, installation, and troubleshooting to help use workforce efficiently.\n"
                "3. **Custom Software Solutions**: Tailored development from desktop/server software to web/mobile apps, BI, and ERP integration.\n"
                "We use high-performance methodologies and prioritize face-to-face interaction over excessive documentation."
            ),
        },
        {
            "title": "products",
            "keywords": ["products", "identity", "kiyos", "ari", "siem", "authnac", "security", "platform"],
            "answer": (
                "Our key products and R&D projects include:\n"
                "- **KIYOS (Identity Platform)**: Turkey's local identity platform. A secure, flexible solution for Single Sign-On (SSO), "
                "Universal Directory, and Lifecycle Management. It supports OAuth2, OpenID Connect, LDAP, and Radius.\n"
                "- **ARI KONAKLAMA**: Accommodation site detection and digitization system with web-based mobile automation.\n"
                "- **MAKSCYBER SIEM**: Real-time log analysis and threat prevention (Netflow, IPFix, Raw Traffic).\n"
                "- **AuthNAC**: Network Access Control combined with KIYOS for secure authentication."
            ),
        },
        {
            "title": "contact",
            "keywords": ["phone", "telephone", "contact", "address", "location", "email"],
            "answer": (
                "**Phone**: 0(324) 404 0 808\n"
                "**Address**: Mersin University, Çiftlikköy Campus Technopark Administrative Building No:1/109 Pk:33343\n"
                "You can also use the contact form on our website."
            ),
        },
    ],
    "tr": [
        {
            "title": "company_overview",
            "keywords": ["kimdir", "hakkında", "şirket", "misyon", "vizyon", "tarihçe", "ne zaman", "kuruldu", "ne zamandan beri", "hangi yıl"],
            "answer": (
                "Toros Yazılım, 2008 yılında Mersin'de kurulmuştur. "
                "**Misyonumuz**: Güncel teknolojiyi kullanarak yüksek kaliteli çözümler sunmak ve müşteri memnuniyetini maksimize etmektir. "
                "**Vizyonumuz**: Uluslararası bir marka olmak ve Türkiye'nin önde gelen yazılım şirketlerinden biri haline gelmektir. "
                "**İlkelerimiz**: Müşteri Odaklılık, Çözüm Üretme, Takım Çalışması, Öğrenmeye Açıklık."
            ),
        },
        {
            "title": "services",
            "keywords": ["hizmetler", "çözümler", "danışmanlık", "entegrasyon", "yazılım geliştirme"],
            "answer": (
                "Başlıca hizmetlerimiz:\n"
                "1. **Servis Entegrasyonları**: Farklı sistem ve platformların veri entegrasyonu.\n"
                "2. **Bilişim ve Danışmanlık**: Analiz, planlama, optimizasyon, kurulum ve sorun giderme.\n"
                "3. **Özel Yazılım Çözümleri**: Kurumsal firmaların ihtiyaçlarına özel yazılım geliştirme."
            ),
        },
        {
            "title": "products",
            "keywords": ["ürünler", "kiyos", "ari konaklama", "siem", "authnac", "güvenlik"],
            "answer": (
                "Ürünlerimiz ve Ar-Ge projelerimiz:\n"
                "- **KIYOS (Kimlik Yönetim Sistemi)**: Bulut ve web tabanlı uygulamalar için güvenli kimlik çözümü.\n"
                "- **ARI KONAKLAMA**: Konaklama noktası tespiti ve sayısallaştırma otomasyonu.\n"
                "- **MAKSCYBER SIEM**: Gerçek zamanlı log analizi ve tehdit önleme (Netflow, IPFix).\n"
                "- **AuthNAC**: KIYOS ve NAC ürünlerinin birleşimiyle güvenli kimlik doğrulama ve erişim kontrolü."
            ),
        },
        {
            "title": "contact",
            "keywords": ["telefon", "iletişim", "adres", "nerede", "konum"],
            "answer": (
                "**Telefon**: 0(324) 404 0 808\n"
                "**Adres**: Mersin Üniversitesi Çiftlikköy Kampüsü Teknopark İdari Bina No:1/109 Pk:33343\n"
                "Web sitemizdeki iletişim formunu da kullanabilirsiniz."
            ),
        },
    ],
    # Keeping minimal placeholders for RU/AR to save space, but logically they should be updated too.
    "ru": [
        {
            "title": "company_overview",
            "keywords": ["кто", "компания", "о нас", "миссия"],
            "answer": _answer_about_toros("ru"),
        },
        {
            "title": "services",
            "keywords": ["услуги", "решения", "что вы предлагаете"],
            "answer": "Мы предлагаем системную интеграцию, IT-консалтинг и разработку заказного ПО.",
        },
        {
             "title": "products",
             "keywords": ["продукты", "kiyos", "siem", "authnac"],
             "answer": "Наши продукты: KIYOS (управление идентификацией), ARI KONAKLAMA, MAKSCYBER SIEM и AuthNAC.",
        },
        {
            "title": "contact",
            "keywords": ["телефон", "контакт", "адрес"],
            "answer": "Телефон: 0(324) 404 0 808. Адрес: Технопарк университета Мерсин.",
        },
    ],
    "ar": [
        {
            "title": "company_overview",
            "keywords": ["من هي", "الشركة", "عن الشركة", "رؤية", "مهمة"],
            "answer": _answer_about_toros("ar"),
        },
        {
             "title": "services",
             "keywords": ["الخدمات", "الحلول", "استشارات", "برمجة"],
             "answer": "نقدم خدمات تكامل الأنظمة، استشارات تكنولوجيا المعلومات، وحلول برمجية مخصصة.",
        },
        {
             "title": "products",
             "keywords": ["المنتجات", "kiyos", "siem", "authnac"],
             "answer": "منتجاتنا تشمل: نظام إدارة الهوية KIYOS، نظام ARI KONAKLAMA، وحلول الأمن السيبراني MAKSCYBER SIEM و AuthNAC.",
        },
        {
             "title": "contact",
             "keywords": ["هاتف", "اتصال", "عنوان", "موقع"],
             "answer": "الهاتف: 0(324) 404 0 808. العنوان: جامعة مرسين، منطقة التكنولوجيا.",
        },
    ],
}


from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# --- TF-IDF Retrieval Logic ---

class TfidfRetriever:
    def __init__(self):
        self.vectorizers: dict[str, TfidfVectorizer] = {}
        self.matrices: dict[str, np.ndarray] = {}
        self.items: dict[str, list[dict[str, Any]]] = {}
        self._build_indices()

    def _build_indices(self):
        """Builds TF-IDF indices for each language in the KNOWLEDGE_BASE."""
        for lang, items in KNOWLEDGE_BASE.items():
            if not items:
                continue
            
            # Construct a rich document for each item to index
            documents = []
            for item in items:
                text_content = (
                    f"{item.get('title', '')} "
                    f"{' '.join(item.get('keywords', []))} "
                    f"{item.get('answer', '')}"
                )
                documents.append(text_content)
            
            if not documents:
                continue

            vec = TfidfVectorizer(stop_words='english' if lang == 'en' else None)
            tfidf_matrix = vec.fit_transform(documents)
            
            self.vectorizers[lang] = vec
            self.matrices[lang] = tfidf_matrix
            self.items[lang] = items

    def find_best_match(self, query: str, language: str) -> str | None:
        """Finds the best matching answer using cosine similarity."""
        vec = self.vectorizers.get(language)
        matrix = self.matrices.get(language)
        items = self.items.get(language)

        if not vec or matrix is None or not items:
            return None

        try:
            query_vec = vec.transform([query])
            cosine_sim = cosine_similarity(query_vec, matrix).flatten()
            best_idx = np.argmax(cosine_sim)
            best_score = cosine_sim[best_idx]
            
            if best_score < 0.15: 
                return None
            
            return items[best_idx]["answer"]
        except Exception:
            return None

# Global retriever instance
_retriever = TfidfRetriever()


def _answer_from_knowledge_base(message: str, language: str) -> str | None:
    """Return the best‑matching knowledge‑base answer using TF-IDF retrieval."""
    return _retriever.find_best_match(message, language)


def _detect_language_from_text(text: str) -> str:
    """Naive language detection for the Toros Yazılım intent only.

    For real production use you would replace this with an ML model or external
    language‑detection service.
    """
    lowered = text.lower()
    # Heuristics based on common phrases / alphabet
    
    # Turkish-specific characters and common words
    turkish_chars = ['ç', 'ğ', 'ı', 'ş', 'ü', 'ö']
    turkish_words = ["kimdir", "yazılım", "yazilim", "nedir", "hakkında", "neler", "merhaba", "naber", "nasıl"]
    
    if any(ch in text for ch in turkish_chars) or any(word in lowered for word in turkish_words):
        return "tr"
    if any(0x600 < ord(ch) < 0x6FF for ch in text):
        # Basic Arabic block check
        return "ar"
    if any(0x400 <= ord(ch) <= 0x4FF for ch in text):
        # Cyrillic block check for Russian
        return "ru"
    return "en"


def _get_language_mismatch_warning(detected_lang: str, selected_lang: str) -> str | None:
    """Generate a warning message when detected language doesn't match selected language."""
    if detected_lang == selected_lang:
        return None
    
    # Map language codes to readable names
    lang_names = {
        "en": {"en": "English", "tr": "İngilizce", "ar": "الإنجليزية", "ru": "Английский"},
        "tr": {"en": "Turkish", "tr": "Türkçe", "ar": "التركية", "ru": "Турецкий"},
        "ar": {"en": "Arabic", "tr": "Arapça", "ar": "العربية", "ru": "Арабский"},
        "ru": {"en": "Russian", "tr": "Rusça", "ar": "الروسية", "ru": "Русский"},
    }
    
    # Warning messages in each language
    warnings = {
        "en": f"It looks like you're typing in {lang_names.get(detected_lang, {}).get('en', detected_lang)}. Would you like to switch to {lang_names.get(detected_lang, {}).get('en', detected_lang)} language?",
        "tr": f"{lang_names.get(detected_lang, {}).get('tr', detected_lang)} dilinde yazıyor gibisiniz. {lang_names.get(detected_lang, {}).get('tr', detected_lang)} diline geçmek ister misiniz?",
        "ar": f"يبدو أنك تكتب بـ{lang_names.get(detected_lang, {}).get('ar', detected_lang)}. هل تريد التبديل إلى {lang_names.get(detected_lang, {}).get('ar', detected_lang)}؟",
        "ru": f"Похоже, вы печатаете на {lang_names.get(detected_lang, {}).get('ru', detected_lang).lower()}. Хотите переключиться на {lang_names.get(detected_lang, {}).get('ru', detected_lang).lower()}?",
    }
    
    return warnings.get(selected_lang, warnings["en"])


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
    
    # Detect actual language of input and check for mismatch
    detected_lang = _detect_language_from_text(raw_message)
    language_warning = _get_language_mismatch_warning(detected_lang, lang)
    
    # If there's a language mismatch, return error message instead of answering
    if language_warning:
        error_messages = {
            "en": "Please switch to the correct language to continue.",
            "tr": "Devam etmek için lütfen doğru dile geçin.",
            "ar": "يرجى التبديل إلى اللغة الصحيحة للمتابعة.",
            "ru": "Пожалуйста, переключитесь на правильный язык, чтобы продолжить.",
        }
        return ChatResponse(
            reply=error_messages.get(lang, error_messages["en"]),
            language=lang,
            suggestions=suggestions,
            language_warning=language_warning
        )

    # Very small intent detection for "Who is Toros Yazilim?"
    # Latin‑script variants (EN/TR/RU suggestion buttons and typed text)
    if "toros yazilim" in normalized or "toros yazılım" in normalized:
        reply_text = _answer_about_toros(lang)
        return ChatResponse(reply=reply_text, language=lang, suggestions=suggestions, language_warning=language_warning)

    # Arabic variant from the Arabic suggestion button / user input.
    if lang == "ar" and ("توروس" in raw_message and "يازليم" in raw_message):
        reply_text = _answer_about_toros("ar")
        return ChatResponse(reply=reply_text, language="ar", suggestions=suggestions, language_warning=language_warning)

    # 1) Intent classification using ML model
    intent_label, confidence = predict_intent(raw_message)

    # 2) Try to answer from the structured knowledge base using the intent.
    #    We look for the KB item whose `title` matches the predicted intent.
    kb_items = KNOWLEDGE_BASE.get(lang, [])
    for item in kb_items:
        if item.get("title") == intent_label:
            return ChatResponse(reply=item["answer"], language=lang, suggestions=suggestions, language_warning=language_warning)

    # 3) If that fails, fall back to similarity search inside the KB.
    kb_answer = _answer_from_knowledge_base(raw_message, lang)
    if kb_answer:
        return ChatResponse(reply=kb_answer, language=lang, suggestions=suggestions, language_warning=language_warning)

    # Fallback behaviour – keep echo‑style reply but still send locale‑specific suggestions.
    reply_text = f"You said: {raw_message}"

    return ChatResponse(reply=reply_text, language=lang, suggestions=suggestions, language_warning=language_warning)
