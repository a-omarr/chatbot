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
    # Link to the official website for additional info
    resource_url: str | None = None


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


BASE_URL: Final = "https://www.torosyazilim.com.tr"

# Mapping intents to their respective pages on the website, localized by language
# tr uses Turkish slugs, while en, ar, ru use English-based slugs as observed on the site.
INTENT_RESOURCE_PATHS: Final = {
    "tr": {
        "services": "hizmetlerimiz",
        "company_overview": "hakkimizda",
        "contact_info": "contact",
        "makscyber_siem": "urunlerimiz",
        "authnac_info": "urunlerimiz",
        "identity_management": "urunler-kimlik-sunucusu",
        "kiyos_features": "urunler-kimlik-sunucusu",
        "ari_konaklama": "https://www.arikonaklama.net/",
        "career_info": "insan-kaynaklari",
        "hiring": "insan-kaynaklari",
        "internship": "staj-imkanlari",
        "custom_software": "hizmetlerimiz",
        "it_consultancy": "hizmetlerimiz",
        "cybersecurity": "hizmetlerimiz",
        "business_clients": "hizmetlerimiz",
        "public_sector": "hakkimizda",
        "products": "urunlerimiz",
        "employees": "hakkimizda",
        "personal_data_protection": "kisisel-verilerin-korunmasi",
        "privacy_policy": "gizlilik-politikasi",
        "user_agreement": "kullanici-sozlesmesi",
        "info_security_policy": "bilgi-guvenligi-politika-ozeti",
        "references": "referanslar",
        "research_development": "arastirma-ve-gelistirme",
        "sales_team": "contact",
        "request_demo": "contact",
        "phone_number": "contact",
    },
    "default": {
        "services": "services",
        "company_overview": "about-us",
        "contact_info": "contact",
        "makscyber_siem": "products",
        "authnac_info": "products",
        "identity_management": "products-identity-server",
        "kiyos_features": "products-identity-server",
        "ari_konaklama": "https://www.arikonaklama.net/",
        "career_info": "human-resources",
        "hiring": "human-resources",
        "internship": "internship-opportunities",
        "custom_software": "services",
        "it_consultancy": "services",
        "cybersecurity": "services",
        "business_clients": "services",
        "public_sector": "about-us",
        "products": "products",
        "employees": "about-us",
        "personal_data_protection": "personal-data-protection",
        "privacy_policy": "privacy-policy",
        "user_agreement": "user-agreement",
        "info_security_policy": "information-security-policy-summary",
        "references": "references",
        "research_development": "research-and-development",
        "sales_team": "contact",
        "request_demo": "contact",
        "phone_number": "contact",
    }
}


# Localized messages for when the bot doesn't recognize the input.
FALLBACK_MESSAGES: dict[str, str] = {
    "en": "You entered an unmeaningful message, please enter a valid message.",
    "tr": "Anlamsız bir mesaj girdiniz, lütfen geçerli bir mesaj giriniz.",
    "ar": "لقد أدخلت رسالة غير مفهومة، يرجى إدخال رسالة صحيحة.",
    "ru": "Вы ввели бессмысленное сообщение, пожалуйста, введите корректное сообщение.",
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
            "Toros Yazılım, 2008 yılında Mersin'de kurulan, web endüstrisiyle ilgili "
            "hemen hemen tüm şirketler için eksiksiz bir hizmet yelpazesi sunan, "
            "müşteri odaklı bir yazılım ve bilişim danışmanlığı şirketidir. "
            "Servis entegrasyonları, bilişim ve danışmanlık hizmetleri, kurumsal "
            "firmalara özel yazılım çözümleri sunar. Teknopark bünyesinde geliştirilen "
            "Kimlik Yönetim Sistemi (KIYOS), ARI Konaklama, MAKSCYBER SIEM ve AuthNAC "
            "gibi Ar‑Ge projeleri ile güvenlik ve kimlik yönetimi çözümleri üretir."
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
                "Our website does not specify an exact number of employees. Toros Yazilim "
                "was founded in 2008 and is composed of a growing team of specialized experts "
                "working in the Mersin Technopark."
            ),
        },
        {
            "title": "services",
            "keywords": ["services", "solutions", "what do you do", "offerings"],
            "answer": (
                "Our main services include:\n"
                "1. **Service Integrations**: Data integration across different systems.\n"
                "2. **IT Consultancy**: Analysis, planning, and optimization.\n"
                "3. **Custom Software**: Tailored solutions for corporate clients."
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
            "keywords": ["contact", "reach out", "address", "location", "where are you", "office"],
            "answer": (
                "📍 **Our Office**:\n"
                "Mersin University Technopark Administrative Building No:1/109, Çiftlikköy Campus, Mersin, Turkey.\n"
                "You can reach us through our contact form or by visiting our office."
            ),
        },
        {
            "title": "sales_team",
            "keywords": ["sales team", "sales department", "sales contact", "talk to sales"],
            "answer": (
                "💼 **Sales Team**: Our specialized sales team is ready to discuss your business needs. "
                "You can contact them directly via **sales@torosyazilim.com.tr** or call our office extension."
            ),
        },
        {
            "title": "request_demo",
            "keywords": ["request a demo", "get a demo", "demo version", "try"],
            "answer": (
                "🧪 **Request a Demo**: Interested in our products? You can request a live demo "
                "by filling out the demo request form on our website or contacting our support team."
            ),
        },
        {
            "title": "phone_number",
            "keywords": ["phone number", "telephone", "call", "contact number"],
            "answer": "📞 **Phone**: You can reach us at **0(324) 404 0 808** during business hours."
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
            "title": "kiyos_features",
            "keywords": ["kiyos features", "identity platform features", "kiyos capabilities", "kiyos functionalities"],
            "answer": (
                "🔑 **KIYOS Features** (Turkey's Local Identity Platform):\n"
                "1. **Yetkim & EduGain Integration**: Ready-made inter-university and inter-institutional integration.\n"
                "2. **Single Sign-On (SSO)**: Access hundreds of apps from a single login point.\n"
                "3. **User Management**: Automated account creation and management from external sources.\n"
                "4. **Lifecycle Management**: Automate access from creation to deletion.\n"
                "5. **Universal Directory Integration**: Active Directory, Azure AD, OpenLDAP sync.\n"
                "6. **Advanced API Management**: API authorization policies based on app, user context, and group membership.\n"
                "7. **Multi-Factor Authentication (MFA)**: Secure employees and users with various MFA factors.\n"
                "8. **Advanced Authentication**: Adaptive, multi-factor identity verification.\n"
                "9. **Identity Management**: Ensure the right people access the right resources.\n"
                "10. **Workflows**: Automate identity processes at scale without code.\n"
                "11. **User Deduplication**: Merge multiple accounts into a single user.\n"
                "12. **Group Management**: Unified mail group control for Google Workspace, Zimbra, etc."
            ),
        },
        {
            "title": "ari_konaklama",
            "keywords": ["ari konaklama", "bee accommodation", "accommodation point detection", "digitization automation"],
            "answer": "🐝 **ARI KONAKLAMA** is our specialized automation project for accommodation point detection and digitization. It streamlines the process of identifying and recording accommodation locations using advanced digitization techniques.",
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
        {
            "title": "personal_data_protection",
            "keywords": ["personal data protection", "kvkk", "gdpr", "data rights", "processing purposes", "data subject rights"],
            "answer": (
                "🛡️ **Personal Data Protection (KVKK)**:\n"
                "TOROS YAZILIM A.Ş. processes your personal data (identity, contact, demographic, platform usage) in compliance with Law No. 6698 (KVKK).\n"
                "- **Purposes**: Communication management, HR processes (internship/job applications), product development, and legal obligations.\n"
                "- **Your Rights**: You can learn if your data is processed, request information, request correction or deletion, and object to automated processing.\n"
                "Applications are processed within 30 days."
            ),
        },
        {
            "title": "privacy_policy",
            "keywords": ["privacy policy", "data collection", "cookies", "analytical purposes"],
            "answer": (
                "🔒 **Privacy Policy**:\n"
                "We collect IP addresses and user agent info via cookies for analytical purposes to improve our services. "
                "Data is processed based on legitimate interest and shared only with authorized partners/institutions when necessary. "
                "Continuing to use the site implies acceptance of this policy."
            ),
        },
        {
            "title": "user_agreement",
            "keywords": ["user agreement", "terms of use", "conditions"],
            "answer": (
                "📜 **User Agreement**:\n"
                "This agreement defines the terms for using our website and services. It covers intellectual property, "
                "user responsibilities, and limitation of liability to ensure a safe and secure experience for all users."
            ),
        },
        {
            "title": "info_security_policy",
            "keywords": ["information security policy", "iso 27001", "security standards", "confidentiality"],
            "answer": (
                "✅ **Information Security Policy**:\n"
                "In line with **ISO 27001:2022**, we commit to protecting the availability, integrity, and confidentiality "
                "of information assets from all internal/external threats. We ensure business continuity and meet "
                "national/international security standards."
            ),
        },
        {
            "title": "references",
            "keywords": ["references", "customers", "partners"],
            "answer": (
                "🤝 **Our References** include prominent institutions such as:\n"
                "- Ankara University\n"
                "- Ankara Hacı Bayram Veli University\n"
                "- Atılım University\n"
                "- Karamanoglu Mehmetbey University\n"
                "- Kirsehir Ahi Evran University\n"
                "- Toros University\n"
                "- T.C. Ministry of Agriculture and Forestry"
            ),
        },
        {
            "title": "research_development",
            "keywords": ["r&d", "research", "development", "innovation"],
            "answer": (
                "🚀 **Research & Development**: We are constantly innovating in cybersecurity and identity management. "
                "Current projects include **AuthNAC** (a combination of KIYOS and NAC features) and advanced real-time log analysis tools. "
                "We focus on OAuth 2.0, OpenID Connect (OIDC), and LDAP standards."
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
            "title": "contact_info",
            "keywords": ["iletişim", "adres", "nerede", "konum", "ofis", "yeriniz neresi"],
            "answer": (
                "📍 **Ofisimiz**:\n"
                "Mersin Üniversitesi Çiftlikköy Kampüsü Teknopark İdari Bina No:1/109 Pk:33343, Mersin.\n"
                "Bize iletişim formumuz üzerinden veya ofisimizi ziyaret ederek ulaşabilirsiniz."
            ),
        },
        {
            "title": "sales_team",
            "keywords": ["satış ekibi", "satış departmanı", "satışla görüşmek", "teklif al"],
            "answer": (
                "💼 **Satış Ekibi**: Uzman satış ekibimiz iş ihtiyaçlarınızı görüşmek için hazır. "
                "Bize **sales@torosyazilim.com.tr** üzerinden mail atabilir veya doğrudan arayabilirsiniz."
            ),
        },
        {
            "title": "request_demo",
            "keywords": ["demo talebi", "demo iste", "denemek istiyorum"],
            "answer": (
                "🧪 **Demo Talebi**: Ürünlerimizi denemek ister misiniz? Web sitemizdeki demo talep formunu "
                "doldurarak veya bizimle iletişime geçerek canlı demo talebinde bulunabilirsiniz."
            ),
        },
        {
            "title": "phone_number",
            "keywords": ["telefon numarası", "telefon", "ara", "iletişim numarası"],
            "answer": "📞 **Telefon**: Mesai saatleri içerisinde bize **0(324) 404 0 808** numarasından ulaşabilirsiniz."
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
            "answer": "👤 **KIYOS** (Kimlik Yönetim Sistemi), Türkiye'nin yerli kimlik platformudur. SSO, MFA ve yaşam döngüsü yönetimi gibi çözümler sunar.",
        },
        {
            "title": "kiyos_features",
            "keywords": ["kiyos özellikleri", "kimlik sunucusu özellikleri", "kiyos ne yapabilir", "kiyos fonksiyonları"],
            "answer": (
                "🔑 **KIYOS Özellikleri** (Türkiye'nin Yerli Kimlik Platformu):\n"
                "1. **Yetkim & EduGain Entegrasyonu**: Üniversiteler ve kurumlar arası hazır entegrasyon altyapısı.\n"
                "2. **Tek Oturum Açma (SSO)**: Tek giriş noktasından yüzlerce uygulamaya erişim.\n"
                "3. **Kullanıcı Yönetimi**: Dış kaynaklardan otomatik hesap oluşturma ve yönetim.\n"
                "4. **Yaşam Döngüsü Yönetimi**: Oluşturmadan silmeye kadar erişimi otomatikleştirin.\n"
                "5. **Universal Dizin Entegrasyonu**: Active Directory, Azure AD, OpenLDAP senkronizasyonu.\n"
                "6. **Gelişmiş API Yönetimi**: Uygulama ve kullanıcı bağlamına dayalı API yetkilendirme ilkeleri.\n"
                "7. **Çok Faktörlü Kimlik Doğrulama (MFA)**: Çeşitli MFA faktörleriyle güvenlik.\n"
                "8. **Gelişmiş Doğrulama**: Uyarlamalı, çok faktörlü kimlik doğrulama.\n"
                "9. **Kimlik Yönetimi**: Doğru kişilerin doğru kaynaklara erişimini sağlayın.\n"
                "10. **İş Akışları**: Kimlik süreçlerini kod yazmadan otomatikleştirin.\n"
                "11. **Kullanıcı Tekilleştirme**: Birden fazla hesabı tek hesapta birleştirin.\n"
                "12. **Grup Yönetimi**: Google Workspace, Zimbra için birleşik grup kontrolü."
            ),
        },
        {
            "title": "ari_konaklama",
            "keywords": ["arı konaklama", "arıkonaklama", "konaklama noktası", "sayısallaştırma otomasyonu"],
            "answer": "🐝 **ARI KONAKLAMA**, konaklama noktası tespiti ve sayısallaştırma otomasyonu projemizdir. Bu çözümle konaklama noktalarının belirlenmesi ve kaydedilmesi süreçlerini dijitalleştirerek hızlandırıyoruz.",
        },
        {
            "title": "career_info",
            "keywords": ["işe alım", "başvuru", "başvurusu", "kariyer", "cv", "insan kaynakları", "staj", "stajyer", "öğrenci"],
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
            "keywords": ["merhaba", "selam", "günaydın", "iyi günler", "hoş geldiniz"],
            "answer": "👋 Merhaba! Toros Yazılım'a hoş geldiniz. Size bugün nasıl yardımcı olabilirim?",
        },
        {
            "title": "personal_data_protection",
            "keywords": ["kişisel verilerin korunması", "kvkk", "veri işleme", "ilgili kişi hakları"],
            "answer": (
                "🛡️ **Kişisel Verilerin Korunması (KVKK)**:\n"
                "TOROS YAZILIM A.Ş., 6698 Sayılı KVKK kapsamında verilerinizi (kimlik, iletişim, platform kullanım verileri) güvenle işlemektedir.\n"
                "- **Amaçlar**: İletişim yönetimi, İK süreçleri, ürün geliştirme ve yasal yükümlülükler.\n"
                "- **Haklarınız**: Verilerinizin işlenip işlenmediğini öğrenme, düzeltme veya silme talebinde bulunma ve itiraz etme hakkınız bulunmaktadır.\n"
                "Başvurularınız en geç 30 gün içinde sonuçlandırılır."
            ),
        },
        {
            "title": "privacy_policy",
            "keywords": ["gizlilik politikası", "çerezler", "analitik"],
            "answer": (
                "🔒 **Gizlilik Politikası**:\n"
                "IP adresiniz ve kullanıcı aracısı bilgileriniz, hizmetlerimizi iyileştirmek için çerezler aracılığıyla analitik amaçlarla işlenir. "
                "Verileriniz meşru menfaat temelinde korunur ve yasal gereklilikler dışında üçüncü taraflarla paylaşılmaz."
            ),
        },
        {
            "title": "user_agreement",
            "keywords": ["kullanıcı sözleşmesi", "kullanım koşulları"],
            "answer": (
                "📜 **Kullanıcı Sözleşmesi**:\n"
                "Web sitemizin ve hizmetlerimizin kullanım şartlarını belirler. Fikri mülkiyet hakları, kullanıcı sorumlulukları "
                "ve sorumluluk sınırlamaları bu sözleşme kapsamında düzenlenmiştir."
            ),
        },
        {
            "title": "info_security_policy",
            "keywords": ["bilgi güvenliği politikası", "iso 27001", "bilgi güvenliği"],
            "answer": (
                "✅ **Bilgi Güvenliği Politikası**:\n"
                "**ISO 27001:2022** standardı uyarınca, bilgi varlıklarının gizliliğini, bütünlüğünü ve erişilebilirliğini "
                "iç/dış tehditlere karşı korumayı taahhüt ediyoruz. İş sürekliliğini sağlıyor ve ulusal/uluslararası standartlara uygun hareket ediyoruz."
            ),
        },
        {
            "title": "references",
            "keywords": ["referanslarımız", "müşteriler", "iş ortakları"],
            "answer": (
                "🤝 **Referanslarımız** arasında şu saygın kurumlar yer almaktadır:\n"
                "- Ankara Üniversitesi\n"
                "- Ankara Hacı Bayram Veli Üniversitesi\n"
                "- Atılım Üniversitesi\n"
                "- Karamanoğlu Mehmetbey Üniversitesi\n"
                "- Kırşehir Ahi Evran Üniversitesi\n"
                "- Toros Üniversitesi\n"
                "- T.C. Tarım ve Orman Bakanlığı"
            ),
        },
        {
            "title": "research_development",
            "keywords": ["ar-ge", "araştırma", "geliştirme", "inovasyon"],
            "answer": (
                "🚀 **Ar-Ge Çalışmalarımız**: Siber güvenlik ve kimlik yönetimi alanlarında sürekli yenilik yapıyoruz. "
                "**AuthNAC** projemiz ve gelişmiş gerçek zamanlı günlük analiz araçları üzerinde çalışmaktayız. "
                "OAuth 2.0, OpenID Connect (OIDC) ve LDAP standartlarını temel alıyoruz."
            ),
        },
        {
            "title": "employees",
            "keywords": ["kaç çalışan", "ekip sayısı", "kadro", "çalışan sayısı"],
            "answer": "Web sitemizde kesin bir çalışan sayısı belirtilmemiştir. Toros Yazılım, 2008 yılından bu yana büyüyen uzman bir kadroya sahiptir.",
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
            "keywords": ["адрес", "где вы", "офис", "местоположение"],
            "answer": (
                "📍 **Наш офис**:\n"
                "Университет Мерсина, Административное здание Технопарка кампуса Чифтликкёй №1/109 Pk:33343.\n"
                "Вы можете связаться с нами через форму обратной связи или посетив наш офис."
            ),
        },
        {
            "title": "sales_team",
            "keywords": ["отдел продаж", "команда продаж", "связаться с продажами"],
            "answer": (
                "💼 **Отдел продаж**: Наша команда готова обсудить ваши потребности. "
                "Пишите нам на **sales@torosyazilim.com.tr**."
            ),
        },
        {
            "title": "request_demo",
            "keywords": ["запросить демо", "демо-версия", "попробовать"],
            "answer": (
                "🧪 **Запросить демо**: Хотите увидеть наши продукты в действии? "
                "Заполните форму на сайте для получения демо-версии."
            ),
        },
        {
            "title": "phone_number",
            "keywords": ["номер телефона", "телефон", "позвонить"],
            "answer": "📞 **Телефон**: Вы можете позвонить нам по номеру **0(324) 404 0 808**."
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
        {
            "title": "kiyos_features",
            "keywords": ["функции kiyos", "возможности платформы", "функционал kiyos"],
            "answer": (
                "🔑 **Функции KIYOS** (Местная платформа идентификации Турции):\n"
                "1. **Интеграция Yetkim & EduGain**: Готовая интеграция между университетами и учреждениями.\n"
                "2. **Единый вход (SSO)**: Доступ к сотням приложений через одну точку входа.\n"
                "3. **Управление пользователями**: Автоматическое создание учётных записей.\n"
                "4. **Управление жизненным циклом**: Автоматизация доступа от создания до удаления.\n"
                "5. **Универсальная интеграция каталогов**: Active Directory, Azure AD, OpenLDAP.\n"
                "6. **Расширенное управление API**: Политики авторизации API на основе контекста.\n"
                "7. **Многофакторная аутентификация (MFA)**: Защита с помощью различных факторов MFA.\n"
                "8. **Управление идентификацией**: Обеспечение доступа нужных людей к нужным ресурсам."
            ),
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
            "keywords": ["عنوان", "موقع", "اين انتم", "مكتب"],
            "answer": (
                "📍 **مكتبنا**:\n"
                "جامعة مرسين، مبنى إدارة التكنوبارك في حرم تشيفتليك كوي رقم 1/109 Pk:33343.\n"
                "يمكنكم التواصل معنا عبر نموذج الاتصال أو زيارة مكتبنا."
            ),
        },
        {
            "title": "sales_team",
            "keywords": ["فريق المبيعات", "قسم المبيعات", "اتصال بالمبيعات"],
            "answer": (
                "💼 **فريق المبيعات**: فريقنا جاهز لمناقشة احتياجاتكم البرمجية. "
                "يمكنكم مراسلتنا عبر **sales@torosyazilim.com.tr**."
            ),
        },
        {
            "title": "request_demo",
            "keywords": ["طلب عرض تجريبي", "نسخة تجريبية", "تجربة"],
            "answer": (
                "🧪 **طلب عرض تجريبي**: هل ترغب في تجربة منتجاتنا؟ "
                "يمكنك طلب عرض مباشر عبر ملء النموذج على موقعنا."
            ),
        },
        {
            "title": "phone_number",
            "keywords": ["رقم الهاتف", "تلفون", "اتصال"],
            "answer": "📞 **الهاتف**: يمكنكم الاتصال بنا على الرقم **0(324) 404 0 808**."
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
            "title": "employees",
            "keywords": ["كم عدد الموظفين", "حجم الفريق", "عدد الموظفين"],
            "answer": "لا يذكر موقعنا عددًا دقيقًا للموظفين. تأسست توروس يازليم في عام 2008 وتضم فريقًا متناميًا من الخبراء في واحة التقنية بمرسين.",
        },
        {
            "title": "greeting",
            "keywords": ["مرحبا", "سلام", "أهلا"],
            "answer": "👋 مرحبًا! أهلاً بكم في توروس يازليم. كيف يمكنني مساعدتكم اليوم؟",
        },
        {
            "title": "kiyos_features",
            "keywords": ["ميزات kiyos", "خصائص منصة الهوية", "وظائف kiyos"],
            "answer": (
                "🔑 **ميزات KIYOS** (منصة الهوية المحلية في تركيا):\n"
                "1. **تكامل Yetkim & EduGain**: بنية تحتية جاهزة للتكامل بين الجامعات والمؤسسات.\n"
                "2. **تسجيل الدخول الموحد (SSO)**: الوصول إلى مئات التطبيقات من نقطة دخول واحدة.\n"
                "3. **إدارة المستخدمين**: إنشاء وإدارة الحسابات تلقائيًا من مصادر خارجية.\n"
                "4. **إدارة دورة الحياة**: أتمتة الوصول من الإنشاء إلى الحذف.\n"
                "5. **تكامل الدليل الشامل**: Active Directory، Azure AD، OpenLDAP.\n"
                "6. **إدارة API المتقدمة**: سياسات تفويض API بناءً على السياق.\n"
                "7. **المصادقة متعددة العوامل (MFA)**: حماية بعوامل MFA متنوعة.\n"
                "8. **إدارة الهوية**: ضمان وصول الأشخاص المناسبين إلى الموارد المناسبة."
            ),
        },
    ],
}


# Global cross-lingual retriever (lazy-built on first call)
_kb_index: KnowledgeIndex | None = None


def _answer_from_knowledge_base(message: str, language: str) -> tuple[str | None, str | None]:
    """Return the (answer, intent_title) from the knowledge base using cross-lingual TF-IDF."""
    global _kb_index
    if _kb_index is None:
        _kb_index = KnowledgeIndex(KNOWLEDGE_BASE)
        _kb_index.build()

    results = _kb_index.retrieve(message, lang=language, top_k=1)
    if not results:
        return None, None

    best = results[0]
    # Similarity threshold: avoid low-quality matches
    if best["score"] < 0.08:
        return None, None

    # Strict language enforcement
    if best.get("lang") != language:
        return None, None

    return best["answer"], best.get("title")


def _detect_language_from_text(text: str) -> str:
    """Robust language detection for Toros Yazılım using scoring-based approach.

    Strips domain-specific brand names first, then counts script-based evidence
    and language-specific keywords to determine the dominant language.
    """
    if not text.strip():
        return "en"

    # 1. Strip domain brand names that appear in all languages to avoid bias
    # (e.g. "Toros Yazilim" is Turkish but used in English questions)
    brand_regex = r"\b(toros|yazilim|kiyos|authnac|makscyber|ari konaklama|siem|demo|api|sso|mfa|edugain|openldap|azure|active directory|google workspace|zimbra)\b"
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
        "kimdir", "nedir", "nediri", "nerde", "nerdedir", "nerede", "neresidir",
        "hakkında", "neler", "sunuyorsunuz", "hizmetleri", "hizmet",
        "projesi", "evet", "hayır", "günaydın", "iyi", "günler", "teklif", "fiyat",
        "ulaşım", "iletişim", "başvuru", "çalışan", "eleman", "sayısı", "kim",
        "talep", "edebilir", "miyim", "misiniz", "musunuz", "yapabilir", "edebilir",
        "istiyorum", "yapıyor", "bilgi", "lütfen", "teşekkür", "ederim", "sağol",
        "var", "yok", "için", "veya", "nasıl", "hangi", "kaç", "ne", "zaman",
        "özellikleri", "çözüm", "çözümleri", "hizmet", "ürün", "ürünler",
        "kuruldu", "kuruluş", "adresi", "yeri", "neresi", "nerede",
    }
    en_words = {
        "hello", "hi", "hey", "how", "who", "what", "about", "which", "where",
        "services", "offer", "provide", "thanks", "thank", "good", "morning",
        "price", "quote", "cost", "hiring", "apply", "contact", "career", "jobs"
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
    def mismatch_response(reply: str = "", intent: str | None = None) -> ChatResponse:
        # Allow the reply even if there's a language mismatch, 
        # as the answer itself will be in the 'lang' (UI) language.
        final_reply = reply
        
        lang_paths = INTENT_RESOURCE_PATHS.get(lang, INTENT_RESOURCE_PATHS["default"])
        resource_path = lang_paths.get(intent) if intent else None
        
        if resource_path:
            if resource_path.startswith("http"):
                resource_url = resource_path
            else:
                resource_url = f"{BASE_URL}/{lang}/{resource_path}"
        else:
            resource_url = None

        return ChatResponse(
            reply=final_reply,
            language=lang,
            suggestions=suggestions,
            language_warning=language_warning,
            is_mismatch=is_mismatch,
            suggested_language=detected_lang,
            resource_url=resource_url
        )

    # 1) Specialized check for basic "Who is Toros Yazilim?" variations
    # (Checking normalized versions and Arabic script)
    if "toros yazilim" in normalized or "toros yazılım" in normalized or \
       (lang == "ar" and "توروس" in raw_message and "يازليم" in raw_message):
        return mismatch_response(_answer_about_toros(lang), intent="company_overview")

    # 2) Intent classification using ML model
    intent_label, confidence = predict_intent(raw_message)

    # 3) High-confidence direct lookup
    # Threshold 0.10 is better for a 16-intent classifier with cross-lingual data.
    if confidence >= 0.10:
        kb_items = KNOWLEDGE_BASE.get(lang, [])
        for item in kb_items:
            if item.get("title") == intent_label:
                return mismatch_response(item["answer"], intent=str(intent_label))

    # 4) Cross-lingual RAG search (fallback)
    kb_answer, kb_intent = _answer_from_knowledge_base(raw_message, lang)
    if kb_answer:
        return mismatch_response(kb_answer, intent=kb_intent)

    # 5) Fallback for unrecognized messages
    # If there's a mismatch and no specific answer found, we suppress the response.
    # Otherwise, we return a localized "I didn't understand" message.
    reply_text = "" if is_mismatch else FALLBACK_MESSAGES.get(lang, FALLBACK_MESSAGES["en"])

    # Log as failed example for active learning if we resort to echo
    if not is_mismatch:
        log_failed_example(FailedExample(
            text=raw_message,
            predicted_intent=str(intent_label),
            language=lang,
            model_confidence=float(confidence)
        ))

    return mismatch_response(reply_text)
