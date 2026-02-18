import asyncio
import sys
import os
import re

# Add the project and backend directory to sys.path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "backend"))

from backend.api.v1.bot import chat, ChatRequest

def normalize_for_test(text: str) -> str:
    """Normalize text for comparison: lowercase and replace Turkish/special chars."""
    if not text:
        return ""
    text = text.lower()
    replacements = {
        "ı": "i", "İ": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g",
        "ü": "u", "Ü": "u", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c",
        "*": "", "#": "", "-": ""
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return " ".join(text.split())

async def run_exhaustive_tests():
    test_suite = {
        "en": [
            ("Who is Toros Yazilim?", "founded in 2008"),
            ("What services do you offer?", "main services include"),
            ("Tell me about KIYOS", "Identity Platform"),
            ("How can I contact your sales team?", "0(324) 404 0 808"),
            ("Are you hiring?", "always looking for talented individuals"),
            ("Do you build mobile apps?", "Web, Mobile, Desktop"),
            ("Tell me about SIEM", "MAKSCYBER SIEM"),
            ("What is AuthNAC?", "Network Access Control"),
            ("How many employees do you have?", "not specify an exact number"),
            ("Do you work with government?", "work with government institutions"),
            ("Hello", "Welcome to Toros Yazilim")
        ],
        "tr": [
            ("Toros Yazılım kimdir?", "2008 yilinda mersin'de kurulan"),
            ("Hangi hizmetleri sunuyorsunuz?", "Servis Entegrasyonlari"),
            ("KIYOS nedir?", "Kimlik Yonetim Sistemi"),
            ("Size nasıl ulaşabilirim?", "0(324) 404 0 808"),
            ("İşe alım yapıyor musunuz?", "Her zaman yetenekli bireyler ariyoruz"),
            ("Mobil uygulama geliştiriyor musunuz?", "Web, Mobil, Masaustu"),
            ("SIEM çözümünüz var mı?", "MAKSCYBER SIEM"),
            ("AuthNAC nedir?", "Ag Erisim Kontrolu"),
            ("Kaç çalışanınız var?", "sayisi belirtilmemistir"),
            ("Kurumsal çözümleriniz neler?", "Kurumsal musterilerimiz için ozel cozumler"),
            ("Merhaba", "Toros Yazilim'a hos geldiniz"),
            ("İş başvurusu nasıl yapabilirim?", "yetenekli bireyler ariyoruz"),
            ("İletişim bilgileriniz?", "0(324) 404 0 808")
        ],
        "ar": [
            ("من هي توروس يازليم؟", "توروس ياز   هي شركة تركية متخصص"),
            ("ما هي خدماتكم؟", "تكامل الأنظمة"),
            ("أخبرني عن KIYOS", "نظام إدارة الهوية"),
            ("كيف أتصل بكم؟", "0(324) 404 0 808"),
            ("فرص عمل", "نحن نبحث دائمًا عن المواهب"),
            ("الأمن السيبراني", "الأمن السيبراني المتقدمة"),
            ("مرحبا", "مرحبًا! أهلاً بكم")
        ],
        "ru": [
            ("Кто такая Toros Yazilim?", "турецкая компания в сфере программного обеспечения"),
            ("Какие услуги вы предлагаете?", "системную интеграцию"),
            ("Расскажите о KIYOS", "управление идентификацией"),
            ("Как с вами связаться?", "0(324) 404 0 808"),
            ("У вас есть вакансии?", "Всегда ищем талантливых"),
            ("Привет", "Привет! Добро пожаловать")
        ]
    }

    total_passed = 0
    total_failed = 0
    
    print("\033[95m" + "="*50 + "\033[0m")
    print("\033[95m" + "   EXHAUSTIVE MULTILINGUAL SYSTEM TESTS   " + "\033[0m")
    print("\033[95m" + "="*50 + "\033[0m\n")

    for lang, cases in test_suite.items():
        print(f"\033[94m--- Language: {lang.upper()} ---\033[0m")
        for query, expected_snippet in cases:
            req = ChatRequest(message=query, language=lang)
            resp = await chat(req)
            
            norm_reply = normalize_for_test(resp.reply)
            norm_expected = normalize_for_test(expected_snippet)

            if norm_expected in norm_reply:
                print(f"✅ \033[92mPASS\033[0m: '{query}'")
                total_passed += 1
            else:
                print(f"❌ \033[91mFAIL\033[0m: '{query}'")
                print(f"   Expected: ...{expected_snippet}...")
                print(f"   Bot Reply: '{resp.reply}'")
                total_failed += 1
        print()

    print("\033[95m" + "="*50 + "\033[0m")
    print(f"   TOTAL PASSED: {total_passed}")
    print(f"   TOTAL FAILED: {total_failed}")
    print("\033[95m" + "="*50 + "\033[0m")
    
    if total_failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_exhaustive_tests())
