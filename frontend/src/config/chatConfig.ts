
export type LocaleCode = 'en' | 'tr' | 'ar' | 'ru';

export interface LocaleConfig {
    code: LocaleCode;
    label: string;
    flag: string;
    suggestions: string[];
}

export const LOCALES: LocaleConfig[] = [
    { code: 'en', label: 'English', flag: '🇬🇧', suggestions: [] },
    { code: 'tr', label: 'Türkçe', flag: '🇹🇷', suggestions: [] },
    { code: 'ar', label: 'العربية', flag: '🇸🇦', suggestions: [] },
    { code: 'ru', label: 'Русский', flag: '🇷🇺', suggestions: [] },
];

export interface Category {
    id: string;
    labels: Record<LocaleCode, string>;
    icon: string;
    questions: Record<LocaleCode, string[]>;
}

export const CATEGORIES: Category[] = [
    {
        id: 'cybersecurity',
        icon: '🛡️',
        labels: { en: 'Cybersecurity Solutions', tr: 'Siber Güvenlik Çözümleri', ar: 'حلول الأمن السيبراني', ru: 'Решения кибербезопасности' },
        questions: {
            en: ['What is Makscyber SIEM?', 'What does AuthNAC do?', 'Do you offer identity management solutions?', "How can I improve my company's cybersecurity?", 'Can I request a demo for your security products?'],
            tr: ['Makscyber SIEM nedir?', 'AuthNAC ne işe yarar?', 'Kimlik yönetimi çözümleri sunuyor musunuz?', 'Şirketimin siber güvenliğini nasıl artırabilirim?', 'Güvenlik ürünleriniz için demo talep edebilir miyim?'],
            ar: ['ما هو Makscyber SIEM؟', 'ماذا يفعل AuthNAC؟', 'هل تقدمون حلول إدارة الهوية؟', 'كيف يمكنني تحسين الأمن السيبراني لشركتي؟', 'هل يمكنني طلب عرض تجريبي لمنتجاتكم؟'],
            ru: ['Что такое Makscyber SIEM?', 'Как работает AuthNAC?', 'Предлагаете ли вы решения для управления идентификацией?', 'Как улучшить кибербезопасность компании?', 'Можно ли заказать демо-версию ваших продуктов?'],
        },
    },
    {
        id: 'business',
        icon: '💼',
        labels: { en: 'Software Development', tr: 'Yazılım Geliştirme', ar: 'تطوير البرمجيات', ru: 'Разработка ПО' },
        questions: {
            en: ['Do you build custom software?', 'Do you develop enterprise software?', 'Can you integrate with our existing systems?', 'Do you provide IT consultancy services?', 'Can I get a project quote?'],
            tr: ['Özel yazılım geliştiriyor musunuz?', 'Kurumsal yazılım geliştiriyor musunuz?', 'Mevcut sistemlerimizle entegre olabilir misiniz?', 'BT danışmanlık hizmeti veriyor musunuz?', 'Proje teklifi alabilir miyim?'],
            ar: ['هل تقومون ببناء برمجيات مخصصة؟', 'هل تطورون برمجيات للمؤسسات؟', 'هل يمكنكم التكامل مع أنظمتنا الحالية؟', 'هل تقدمون خدمات استشارات تكنولوجيا المعلومات؟', 'هل يمكنني الحصول على عرض سعر لمشروع؟'],
            ru: ['Вы занимаетесь разработкой заказного ПО?', 'Вы разрабатываете корпоративное ПО?', 'Можете ли вы интегрироваться с нашими системами?', 'Предоставляете ли вы IT-консалтинговые услуги?', 'Можно ли получить предварительную стоимость проекта?'],
        },
    },
    {
        id: 'corporate',
        icon: '🏛️',
        labels: { en: 'Corporate Services', tr: 'Kurumsal Hizmetler', ar: 'الخدمات المؤسسية', ru: 'Корпоративные услуги' },
        questions: {
            en: ['Who is Toros Yazilim?', 'What services do you offer?', 'Where is Toros Yazilim located?', 'Do you work with government institutions?', 'Are your systems compliant with security standards?'],
            tr: ['Toros Yazılım kimdir?', 'Hangi hizmetleri sunuyorsunuz?', 'Toros Yazılım nerede?', 'Kamu kurumları ile çalışıyor musunuz?', 'Sistemleriniz güvenlik standartlarına uygun mu?'],
            ar: ['من هي توروس يازليم؟', 'ما هي الخدمات التي تقدمونها؟', 'أين تقع شركة توروس يازليم؟', 'هل تعملون مع المؤسسات الحكومية؟', 'هل أنظمتكم متوافقة مع المعايير الأمنية؟'],
            ru: ['Кто такая Toros Yazilim?', 'Какие услуги вы предлагаете?', 'Где находится Toros Yazilim?', 'Работаете ли вы с государственными учреждениями?', 'Соответствуют ли ваши системы стандартам безопасности?'],
        },
    },
    {
        id: 'contact',
        icon: '📞',
        labels: { en: 'Contact & Demo', tr: 'İletişim ve Demo', ar: 'الاتصال والعرض التجريبي', ru: 'Контакт и демо' },
        questions: {
            en: ['How can I contact you?', 'How can I contact your sales team?', 'What is your phone number?', 'Can I request a demo?'],
            tr: ['Size nasıl ulaşabilirim?', 'Satış ekibinize nasıl ulaşabilirim?', 'Telefon numaranız nedir?', 'Demo talep edebilir miyim?'],
            ar: ['كيف يمكنني الاتصال بكم؟', 'كيف يمكنني الاتصال بفريق المبيعات؟', 'ما هو رقم هاتفكم؟', 'هل يمكنني طلب عرض تجريبي؟'],
            ru: ['Как с вами связаться?', 'Как связаться с отделом продаж?', 'Какой у вас номер телефона?', 'Можно ли заказать демо?'],
        },
    },
    {
        id: 'careers',
        icon: '👨‍💻',
        labels: { en: 'Careers', tr: 'Kariyer', ar: 'الوظائف', ru: 'Карьера' },
        questions: {
            en: ['Are you hiring?', 'Do you offer internships?', 'How can I apply for a job?'],
            tr: ['İşe alım yapıyor musunuz?', 'Staj imkanı sunuyor musunuz?', 'İş başvurusu nasıl yapabilirim?'],
            ar: ['هل لديكم وظائف شاغرة؟', 'هل تقدمون فرص تدريب؟', 'كيف يمكنني التقدم لوظيفة؟'],
            ru: ['У вас есть вакансии?', 'Предлагаете ли вы стажировки?', 'Как я могу подать заявку на работу?'],
        },
    },
];

export const welcomeMessages: Record<LocaleCode, string> = {
    en: '👋 Welcome to Toros Yazılım.\nHow can we assist you today?\nChoose a topic below or type your question.',
    tr: "👋 Toros Yazılım'a hoş geldiniz.\nSize bugün nasıl yardımcı olabiliriz?\nAşağıdan bir konu seçin veya sorunuzu yazın.",
    ar: '👋 مرحبًا بكم في توروس يازليم.\nكيف يمكننا مساعدتكم اليوم؟\nاختاروا موضوعًا أدناه أو اكتبوا سؤالكم.',
    ru: '👋 Добро пожаловать в Toros Yazılım.\nЧем мы можем вам помочь сегодня?\nВыберите тему ниже или напишите свой вопрос.',
};

export const COMPANY_LOGO_URL = 'https://www.torosyazilim.com.tr/images/toros-yazilim-normal.svg';
export const DEFAULT_API_URL = '/api/v1/bot/chat';
