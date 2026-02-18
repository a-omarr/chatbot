from __future__ import annotations
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Final
import logging
import re

from app.ml.intent_classifier import predict_intent
from app.ml.rag_engine import KnowledgeIndex
from app.ml.active_learning import log_failed_example, FailedExample


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
    # Flag to indicate language detection mismatch
    is_mismatch: bool = False
    # The language code that was actually detected (e.g. "tr")
    suggested_language: str | None = None


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
            "title": "contact_info",
            "keywords": [
                "phone", "telephone", "call you", "contact number", "address", "location", 
                "where are you", "office", "technopark", "sales team", "hire us", "quote", 
                "demo", "buy", "request a demo", "get started", "contact"
            ],
            "answer": (
                "**Phone**: 0(324) 404 0 808\n"
                "**Address**: Mersin University, Çiftlikköy Campus Technopark Administrative Building No:1/109 Pk:33343\n"
                "To reach our sales team or request a demo, please use the contact form on our website or call us directly."
            ),
        },
        {
            "title": "makscyber_siem",
            "keywords": ["makscyber", "siem", "log analysis", "threat prevention"],
            "answer": "🛡️ **MAKSCYBER SIEM** is our real-time log analysis and threat prevention solution. It monitors Netflow, IPFix, and Raw Traffic to secure your infrastructure.",
        },
        {
            "title": "authnac_info",
            "keywords": ["authnac", "network access control", "secure authentication"],
            "answer": "🔐 **AuthNAC** is our Network Access Control solution. When combined with KIYOS, it provides robust secure authentication for your entire network.",
        },
        {
            "title": "identity_management",
            "keywords": ["identity management", "sso", "mfa", "kiyos", "universal directory"],
            "answer": "👤 **KIYOS** is our flagship Identity Platform, offering Single Sign-On (SSO), MFA, and Lifecycle Management. It's Turkey's leading local identity solution.",
        },
        {
            "title": "career_info",
            "keywords": ["hiring", "jobs", "apply", "career", "human resources", "cv", "internship", "student", "intern", "program"],
            "answer": (
                "We are always looking for talented individuals!\n"
                "- **Apply**: Send your CV through our website's career portal or via email.\n"
                "- **Internships**: We offer internship opportunities for students throughout the year."
            ),
        },
        {
            "title": "custom_software",
            "keywords": ["custom software", "build app", "develop", "software development"],
            "answer": "💻 We develop custom, scalable software solutions (Web, Mobile, Desktop) tailored to your specific business needs and high-performance requirements.",
        },
        {
            "title": "it_consultancy",
            "keywords": ["it consultancy", "analysis", "planning", "optimization"],
            "answer": "📊 Our IT consultancy services include analysis, planning, and optimization to help your company use its workforce and technology efficiently.",
        },
        {
            "title": "cybersecurity",
            "keywords": ["makscyber", "siem", "authnac", "security", "threat", "log analysis", "improve cybersecurity", "demo"],
            "answer": (
                "Toros Yazılım provides advanced cybersecurity solutions:\n"
                "- **MAKSCYBER SIEM**: Real-time log analysis and threat prevention (Netflow, IPFix).\n"
                "- **AuthNAC**: Combined with KIYOS for secure authentication and network access control.\n"
                "- **Identity Management**: KIYOS platform for SSO, MFA, and Lifecycle Management.\n"
                "You can improve your company’s security by implementing these localized and high-performance solutions. **Contact us for a demo!**"
            ),
        },
        {
            "title": "business_clients",
            "keywords": ["enterprise software", "integrate", "existing systems", "it consultancy", "quote", "how long", "project"],
            "answer": (
                "We offer tailored solutions for business clients:\n"
                "- **Enterprise Software**: We develop custom scalable software (Web, Mobile, Desktop).\n"
                "- **System Integration**: We can integrate new solutions with your existing infrastructure.\n"
                "- **IT Consultancy**: Analysis, planning, and optimization services.\n"
                "- **Process**: Project duration and quotes depend on the scope. Contact us for a detailed project evaluation."
            ),
        },
        {
            "title": "public_sector",
            "keywords": ["government", "institutions", "on-premise", "compliance", "security standards"],
            "answer": (
                "Yes, we work with government institutions and municipalities, offering:\n"
                "- **On-premise Solutions**: For high-security requirements and data sovereignty.\n"
                "- **Compliance**: Our systems are developed and audited according to national and international security standards."
            ),
        },
        {
            "title": "greeting",
            "keywords": ["hello", "hi", "hey", "good morning", "good afternoon", "welcome"],
            "answer": "👋 Hello! Welcome to Toros Yazılım. How can I assist you today?",
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
            "title": "contact_info",
            "keywords": ["telefon", "iletişim", "adres", "nerede", "konum", "satış ekibi", "teklif", "fiyat", "demo", "satın al"],
            "answer": (
                "**Telefon**: 0(324) 404 0 808\n"
                "**Adres**: Mersin Üniversitesi Çiftlikköy Kampüsü Teknopark İdari Bina No:1/109 Pk:33343\n"
                "Satış ekibimize ulaşmak veya demo talebinde bulunmak için lütfen web sitemizdeki iletişim formunu kullanın veya bizi doğrudan arayın."
            ),
        },
        {
            "title": "cybersecurity",
            "keywords": ["makscyber", "siem", "authnac", "siber güvenlik", "tehdit", "günlük analizi", "demo"],
            "answer": (
                "Toros Yazılım gelişmiş siber güvenlik çözümleri sunar:\n"
                "- **MAKSCYBER SIEM**: Gerçek zamanlı log analizi ve tehdit önleme (Netflow, IPFix).\n"
                "- **AuthNAC**: Güvenli kimlik doğrulama ve ağ erişim kontrolü için KIYOS ile entegre çözüm.\n"
                "- **Kimlik Yönetimi**: SSO, MFA ve Yaşam Döngüsü Yönetimi için KIYOS platformu.\n"
                "Yerli ve yüksek performanslı çözümlerimizle şirketinizin güvenliğini artırabilirsiniz. **Demo için bizimle iletişime geçin!**"
            ),
        },
        {
            "title": "business_clients",
            "keywords": ["kurumsal yazılım", "entegrasyon", "mevcut sistemler", "bt danışmanlık", "teklif", "ne kadar sürer", "proje"],
            "answer": (
                "Kurumsal müşterilerimiz için özel çözümler sunuyoruz:\n"
                "- **Kurumsal Yazılım**: Ölçeklenebilir web, mobil ve masaüstü yazılım geliştirme.\n"
                "- **Sistem Entegrasyonu**: Yeni çözümlerin mevcut altyapınıza entegrasyonu.\n"
                "- **BT Danışmanlığı**: Analiz, planlama ve optimizasyon hizmetleri.\n"
                "- **Süreç**: Proje süreleri ve teklifler kapsamına göre değişir. Detaylı değerlendirme için bizimle iletişime geçebilirsiniz."
            ),
        },
        {
            "title": "public_sector",
            "keywords": ["kamu", "kurumlar", "yerinde", "on-premise", "uyumluluk", "güvenlik standartları"],
            "answer": (
                "Evet, kamu kurumları ile çalışıyoruz ve şunları sunuyoruz:\n"
                "- **On-premise Çözümler**: Yüksek güvenlik gereksinimleri için yerinde kurulum.\n"
                "- **Uyumluluk**: Sistemlerimiz ulusal ve uluslararası güvenlik standartlarına uygun olarak geliştirilmektedir."
            ),
        },
        {
            "title": "makscyber_siem",
            "keywords": ["makscyber", "siem", "log analizi", "tehdit önleme"],
            "answer": "🛡️ **MAKSCYBER SIEM**, gerçek zamanlı log analizi ve tehdit önleme çözümümüzdür. Altyapınızı güvence altına almak için trafik verilerini izler.",
        },
        {
            "title": "authnac_info",
            "keywords": ["authnac", "ağ erişim kontrolü", "güvenli kimlik doğrulama"],
            "answer": "🔐 **AuthNAC**, Ağ Erişim Kontrolü çözümümüzdür. KIYOS ile birlikte kullanıldığında ağınız için tam güvenlik sağlar.",
        },
        {
            "title": "identity_management",
            "keywords": ["kimlik yönetimi", "sso", "mfa", "kiyos", "tek oturum açma"],
            "answer": "👤 **KIYOS**, Türkiye'nin yerli kimlik platformudur. SSO, MFA ve yaşam döngüsü yönetimi gibi çözümler sunar.",
        },
        {
            "title": "career_info",
            "keywords": ["işe alım", "başvuru", "kariyer", "cv", "insan kaynakları", "staj", "stajyer", "öğrenci"],
            "answer": (
                "Her zaman yetenekli bireyler arıyoruz!\n"
                "- **Başvuru**: CV'nizi web sitemizin kariyer portalı üzerinden veya e-posta yoluyla gönderin.\n"
                "- **Staj**: Öğrenciler için yıl boyunca staj imkanları sunuyoruz."
            ),
        },
        {
            "title": "custom_software",
            "keywords": ["özel yazılım", "uygulama geliştirme", "kodlama"],
            "answer": "💻 İş ihtiyaçlarınıza özel, ölçeklenebilir yazılım çözümleri (Web, Mobil, Masaüstü) geliştiriyoruz.",
        },
        {
            "title": "it_consultancy",
            "keywords": ["bt danışmanlık", "analiz", "planlama", "optimizasyon"],
            "answer": "📊 BT danışmanlık hizmetlerimizle, iş gücünüzü ve teknolojinizi en verimli şekilde kullanmanıza yardımcı oluyoruz.",
        },
        {
            "title": "greeting",
            "keywords": ["merhaba", "selam", "günaydın", "iyi günler", "hoш geldiniz"],
            "answer": "👋 Merhaba! Toros Yazılım'a hoş geldiniz. Size bugün nasıl yardımcı olabilirim?",
        },
    ],
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
            "title": "cybersecurity",
            "keywords": ["siem", "authnac", "безопасность"],
            "answer": "Мы предлагаем решения для кибербезопасности, такие как MAKSCYBER SIEM и AuthNAC.",
        },
        {
            "title": "business_clients",
            "keywords": ["корпоративное по", "бизнес"],
            "answer": "Мы разрабатываем индивидуальное программное обеспечение для корпоративных клиентов.",
        },
        {
            "title": "contact_info",
            "keywords": ["телефон", "адрес", "связаться", "контакты", "демо"],
            "answer": (
                "**Телефон**: 0(324) 404 0 808\n"
                "**Адрес**: Университет Мерсина, Административное здание Технопарка кампуса Чифтликкёй №1/109 Pk:33343\n"
                "Чтобы связаться с нашим отделом продаж или запросить демо-версию, пожалуйста, используйте форму обратной связи на нашем сайте или позвоните нам напрямую."
            ),
        },
        {
            "title": "career_info",
            "keywords": ["работа", "вакансии", "стажировка"],
            "answer": (
                "Мы всегда ищем талантливых специалистов!\n"
                "- **Подать заявку**: Отправьте свое резюме через карьерный портал нашего сайта или по электронной почте.\n"
                "- **Стажировки**: Мы предлагаем возможности стажировки для студентов в течение всего года."
            ),
        },
        {
            "title": "greeting",
            "keywords": ["привет", "здравствуйте", "добрый день"],
            "answer": "👋 Привет! Добро пожаловать в Toros Yazılım. Чем я могу вам помочь сегодня?",
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
            "title": "contact_info",
            "keywords": ["هاتف", "اتصال", "عنوان", "موقع", "تجريبي", "مبيعات"],
            "answer": (
                "**الهاتف**: 0(324) 404 0 808\n"
                "**العنوان**: جامعة مرسين، مبنى إدارة التكنوبارك في حرم تشيفتليك كوي رقم 1/109 Pk:33343\n"
                "للتواصل مع فريق المبيعات لدينا أو طلب عرض تجريبي، يرجى استخدام نموذج الاتصال على موقعنا الإلكتروني أو الاتصال بنا مباشرة."
            ),
        },
        {
            "title": "cybersecurity",
            "keywords": ["الأمن السيبراني", "siem", "authnac"],
            "answer": "نحن نقدم حلول الأمن السيبراني المتقدمة مثل MAKSCYBER SIEM و AuthNAC.",
        },
        {
            "title": "business_clients",
            "keywords": ["حلول الشركات", "برمجيات المؤسسات"],
            "answer": "نحن نطور برمجيات مخصصة للشركات والمؤسسات الكبيرة.",
        },
        {
            "title": "career_info",
            "keywords": ["وظائف", "توظيف", "تدريب", "سيرة ذاتية"],
            "answer": (
                "نحن نبحث دائمًا عن المواهب!\n"
                "- **تقديم**: أرسل سيرتك الذاتية عبر بوابة التوظيف في موقعنا الإلكتروني أو عبر البريد الإلكتروني.\n"
                "- **التدريب**: نقدم فرص تدريب للطلاب على مدار العام."
            ),
        },
        {
            "title": "greeting",
            "keywords": ["مرحبا", "سلام", "أهلا"],
            "answer": "👋 مرحبًا! أهلاً بكم في توروس يازليم. كيف يمكنني مساعدتكم اليوم؟",
        },
    ],
}


# Global cross-lingual retriever (lazy-built on first call)
_kb_index: KnowledgeIndex | None = None


def _answer_from_knowledge_base(message: str, language: str) -> str | None:
    """Return the best‑matching knowledge‑base answer using cross-lingual TF-IDF."""
    global _kb_index
    if _kb_index is None:
        _kb_index = KnowledgeIndex(KNOWLEDGE_BASE)
        _kb_index.build()

    results = _kb_index.retrieve(message, lang=language, top_k=1)
    if not results:
        return None

    best = results[0]
    # Similarity threshold: avoid low-quality matches
    if best["score"] < 0.08:
        return None

    # Strict language enforcement: Ensure the RAG answer matches the requested session language.
    # This prevents Turkish KB results from showing up in English sessions if detection fails.
    if best.get("lang") != language:
        return None

    return best["answer"]


def _detect_language_from_text(text: str) -> str:
    """Robust language detection for Toros Yazılım using scoring-based approach.

    Strips domain-specific brand names first, then counts script-based evidence
    and language-specific keywords to determine the dominant language.
    """
    if not text.strip():
        return "en"

    # 1. Strip domain brand names that appear in all languages to avoid bias
    # (e.g. "Toros Yazilim" is Turkish but used in English questions)
    brand_regex = r"\b(toros|yazilim|kiyos|authnac|makscyber|ari konaklama)\b"
    clean_text = re.sub(brand_regex, "", text, flags=re.IGNORECASE).lower()

    # 2. Scoring system
    scores = {"en": 0, "tr": 0, "ar": 0, "ru": 0}

    # --- Script Evidence (Higher weight) ---
    # Arabic block
    if any("\u0600" <= ch <= "\u06FF" for ch in text):
        scores["ar"] += 5
    # Cyrillic block
    if any("\u0400" <= ch <= "\u04FF" for ch in text):
        scores["ru"] += 5
    # Turkish-specific characters
    turkish_specific_chars = ["ç", "ğ", "ı", "ş", "ö", "ü"]
    if any(ch in clean_text for ch in turkish_specific_chars):
        scores["tr"] += 4

    # --- Word Evidence (Lower weight) ---
    # Expanded list including common typos and greeting variants
    tr_words = {
        "merhaba", "merahaba", "merhablar", "selam", "selamlar", "nasıl", 
        "kimdir", "nedir", "hakkında", "neler", "sunuyorsunuz", "hizmetleri", 
        "projesi", "evet", "hayır", "günaydın", "iyi", "günler"
    }
    en_words = {
        "hello", "hi", "hey", "how", "who", "what", "about", "which", 
        "services", "offer", "provide", "thanks", "thank", "good", "morning"
    }
    
    words = set(re.findall(r"\w+", clean_text))
    for word in words:
        if word in tr_words:
            scores["tr"] += 2
        if word in en_words:
            scores["en"] += 2

    # If no strong signal, and text uses Latin script, default based on word count
    # Most general technical/company questions in the absence of TR markers are likely EN
    if max(scores.values()) == 0:
        return "en"

    return max(scores, key=lambda l: scores[l])


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
    is_mismatch = (detected_lang != lang)
    language_warning = _get_language_mismatch_warning(detected_lang, lang) if is_mismatch else None
    
    # helper for mismatch responses
    def mismatch_response(reply: str = "") -> ChatResponse:
        # Strictly enforce: no reply if there's a language mismatch
        # This prevents the bot from answering in a different language than the UI context.
        final_reply = "" if is_mismatch else reply
        
        return ChatResponse(
            reply=final_reply,
            language=lang,
            suggestions=suggestions,
            language_warning=language_warning,
            is_mismatch=is_mismatch,
            suggested_language=detected_lang
        )

    # 1) Specialized check for basic "Who is Toros Yazilim?" variations
    # (Checking normalized versions and Arabic script)
    if "toros yazilim" in normalized or "toros yazılım" in normalized or \
       (lang == "ar" and "توروس" in raw_message and "يازليم" in raw_message):
        return mismatch_response(_answer_about_toros(lang))

    # 2) Intent classification using ML model
    intent_label, confidence = predict_intent(raw_message)

    # 3) High-confidence direct lookup
    if confidence >= 0.3:
        kb_items = KNOWLEDGE_BASE.get(lang, [])
        for item in kb_items:
            if item.get("title") == intent_label:
                return mismatch_response(item["answer"])

    # 4) Cross-lingual RAG search (fallback)
    kb_answer = _answer_from_knowledge_base(raw_message, lang)
    if kb_answer:
        return mismatch_response(kb_answer)

    # 5) Echo fallback
    # If there's a mismatch and no specific answer found, we suppress the echo
    # to avoid "You said: hello" when the user likely made a language mistake.
    reply_text = "" if is_mismatch else f"You said: {raw_message}"

    # Log as failed example for active learning if we resort to echo
    if not is_mismatch:
        log_failed_example(FailedExample(
            text=raw_message,
            predicted_intent=str(intent_label),
            language=lang,
            model_confidence=float(confidence)
        ))

    return mismatch_response(reply_text)
