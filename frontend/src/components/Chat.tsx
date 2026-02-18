import React, { useState } from 'react';

export interface Message {
  id: number;
  role: 'user' | 'bot';
  text: string;
}

interface ChatApiResponse {
  reply: string;
  language?: string | null;
  suggestions?: string[] | null;
  language_warning?: string | null;
}

interface ChatProps {
  /** Optional override for the API URL. Defaults to FastAPI v1 bot endpoint. */
  apiUrl?: string;
}

const DEFAULT_API_URL = '/api/v1/bot/chat';

type LocaleCode = 'en' | 'tr' | 'ar' | 'ru';

interface LocaleConfig {
  code: LocaleCode;
  label: string;
  flag: string;
  suggestions: string[];
}

const LOCALES: LocaleConfig[] = [
  {
    code: 'en',
    label: 'English',
    flag: '🇬🇧',
    suggestions: [], // Replaced by CATEGORIES
  },
  {
    code: 'tr',
    label: 'Türkçe',
    flag: '🇹🇷',
    suggestions: [],
  },
  {
    code: 'ar',
    label: 'العربية',
    flag: '🇸🇦',
    suggestions: [],
  },
  {
    code: 'ru',
    label: 'Русский',
    flag: '🇷🇺',
    suggestions: [],
  },
];

interface Category {
  id: string;
  labels: Record<LocaleCode, string>;
  icon: string;
  questions: Record<LocaleCode, string[]>;
}

const CATEGORIES: Category[] = [
  {
    id: 'cybersecurity',
    icon: '🛡️',
    labels: { en: 'Cybersecurity Solutions', tr: 'Siber Güvenlik Çözümleri', ar: 'حلول الأمن السيبراني', ru: 'Решения кибербезопасности' },
    questions: {
      en: [
        'What is Makscyber SIEM?',
        'What does AuthNAC do?',
        'Do you offer identity management solutions?',
        'How can I improve my company’s cybersecurity?',
        'Can I request a demo for your security products?',
      ],
      tr: [
        'Makscyber SIEM nedir?',
        'AuthNAC ne işe yarar?',
        'Kimlik yönetimi çözümleri sunuyor musunuz?',
        'Şirketimin siber güvenliğini nasıl artırabilirim?',
        'Güvenlik ürünleriniz için demo talep edebilir miyim?',
      ],
      ar: [
        'ما هو Makscyber SIEM؟',
        'ماذا يفعل AuthNAC؟',
        'هل تقدمون حلول إدارة الهوية؟',
        'كيف يمكنني تحسين الأمن السيبراني لشركتي؟',
        'هل يمكنني طلب عرض تجريبي لمنتجاتكم؟',
      ],
      ru: [
        'Что такое Makscyber SIEM?',
        'Как работает AuthNAC?',
        'Предлагаете ли вы решения для управления идентификацией?',
        'Как улучшить кибербезопасность компании?',
        'Можно ли заказать демо-версию ваших продуктов?',
      ],
    },
  },
  {
    id: 'business',
    icon: '💼',
    labels: { en: 'Software Development', tr: 'Yazılım Geliştirme', ar: 'تطوير البرمجيات', ru: 'Разработка ПО' },
    questions: {
      en: [
        'Do you build custom software?',
        'Do you develop enterprise software?',
        'Can you integrate with our existing systems?',
        'Do you provide IT consultancy services?',
        'Can I get a project quote?',
      ],
      tr: [
        'Özel yazılım geliştiriyor musunuz?',
        'Kurumsal yazılım geliştiriyor musunuz?',
        'Mevcut sistemlerimizle entegre olabilir misiniz?',
        'BT danışmanlık hizmeti veriyor musunuz?',
        'Proje teklifi alabilir miyim?',
      ],
      ar: [
        'هل تقومون ببناء برمجيات مخصصة؟',
        'هل تطورون برمجيات للمؤسسات؟',
        'هل يمكنكم التكامل مع أنظمتنا الحالية؟',
        'هل تقدمون خدمات استشارات تكنولوجيا المعلومات؟',
        'هل يمكنني الحصول على عرض سعر لمشروع؟',
      ],
      ru: [
        'Вы занимаетесь разработкой заказного ПО?',
        'Вы разрабатываете корпоративное ПО?',
        'Можете ли вы интегрироваться с нашими системами?',
        'Предоставляете ли вы IT-консалтинговые услуги?',
        'Можно ли получить предварительную стоимость проекта?',
      ],
    },
  },
  {
    id: 'corporate',
    icon: '🏛️',
    labels: { en: 'Corporate Services', tr: 'Kurumsal Hizmetler', ar: 'الخدمات المؤسسية', ru: 'Корпоративные услуги' },
    questions: {
      en: [
        'Who is Toros Yazilim?',
        'What services do you offer?',
        'Where is Toros Yazilim located?',
        'Do you work with government institutions?',
        'Are your systems compliant with security standards?',
      ],
      tr: [
        'Toros Yazılım kimdir?',
        'Hangi hizmetleri sunuyorsunuz?',
        'Toros Yazılım nerede?',
        'Kamu kurumları ile çalışıyor musunuz?',
        'Sistemleriniz güvenlik standartlarına uygun mu?',
      ],
      ar: [
        'من هي توروس يازليم؟',
        'ما هي الخدمات التي تقدمونها؟',
        'أين تقع شركة توروس يازليم؟',
        'هل تعملون مع المؤسسات الحكومية؟',
        'هل أنظمتكم متوافقة مع المعايير الأمنية؟',
      ],
      ru: [
        'Кто такая Toros Yazilim?',
        'Какие услуги вы предлагаете?',
        'Где находится Toros Yazilim?',
        'Работаете ли вы с государственными учреждениями?',
        'Соответствуют ли ваши системы стандартам безопасности?',
      ],
    },
  },
  {
    id: 'contact',
    icon: '📞',
    labels: { en: 'Contact & Demo', tr: 'İletişim ve Demo', ar: 'الاتصال والعرض التجريبي', ru: 'Контакт и демо' },
    questions: {
      en: [
        'How can I contact you?',
        'How can I contact your sales team?',
        'What is your phone number?',
        'Can I request a demo?',
      ],
      tr: [
        'Size nasıl ulaşabilirim?',
        'Satış ekibinize nasıl ulaşabilirim?',
        'Telefon numaranız nedir?',
        'Demo talep edebilir miyim?',
      ],
      ar: [
        'كيف يمكنني الاتصال بكم؟',
        'كيف يمكنني الاتصال بفريق المبيعات؟',
        'ما هو رقم هاتفكم؟',
        'هل يمكنني طلب عرض تجريبي؟',
      ],
      ru: [
        'Как с вами связаться?',
        'Как связаться с отделом продаж?',
        'Какой у вас номер телефона?',
        'Можно ли заказать демо?',
      ],
    },
  },
  {
    id: 'careers',
    icon: '👨‍💻',
    labels: { en: 'Careers', tr: 'Kariyer', ar: 'الوظائف', ru: 'Карьера' },
    questions: {
      en: [
        'Are you hiring?',
        'Do you offer internships?',
        'How can I apply for a job?',
      ],
      tr: [
        'İşe alım yapıyor musunuz?',
        'Staj imkanı sunuyor musunuz?',
        'İş başvurusu nasıl yapabilirim?',
      ],
      ar: [
        'هل لديكم وظائف شاغرة؟',
        'هل تقدمون فرص تدريب؟',
        'كيف يمكنني التقدم لوظيفة؟',
      ],
      ru: [
        'У вас есть вакансии?',
        'Предлагаете ли вы стажировки?',
        'Как я могу подать заявку на работу?',
      ],
    },
  },
];

const findLocale = (code: LocaleCode): LocaleConfig =>
  LOCALES.find((l) => l.code === code) ?? LOCALES[0];

const Chat: React.FC<ChatProps> = ({ apiUrl = DEFAULT_API_URL }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeLocale, setActiveLocale] = useState<LocaleCode>('en');
  const [activeCategoryId, setActiveCategoryId] = useState<string | null>(null);
  const [languageWarning, setLanguageWarning] = useState<string | null>(null);

  const welcomeMessages: Record<LocaleCode, string> = {
    en: '👋 Welcome to Toros Yazılım.\nHow can we assist you today?\nYou can choose one of the options below or type your question.',
    tr: '👋 Toros Yazılım\'a hoş geldiniz.\nSize bugün nasıl yardımcı olabiliriz?\nAşağıdaki seçeneklerden birini seçebilir veya sorunuzu yazabilirsiniz.',
    ar: '👋 مرحبًا بكم في توروس يازليم.\nكيف يمكننا مساعدتكم اليوم؟\nيمكنكم اختيار أحد الخيارات أدناه أو كتابة سؤالكم.',
    ru: '👋 Добро пожаловать в Toros Yazılım.\nЧем мы можем вам помочь сегодня?\nВы можете выбрать один из вариантов ниже или написать свой вопрос.',
  };

  const sendMessage = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    setError(null);

    const userMessage: Message = {
      id: Date.now(),
      role: 'user',
      text: trimmed,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed, language: activeLocale }),
      });

      if (!res.ok) {
        throw new Error(`Request failed with status ${res.status}`);
      }

      const data: ChatApiResponse = await res.json();

      const botMessage: Message = {
        id: Date.now() + 1,
        role: 'bot',
        text: data.reply,
      };

      setMessages((prev) => [...prev, botMessage]);

      // Handle language warning
      if (data.language_warning) {
        setLanguageWarning(data.language_warning);
      }
    } catch (err) {
      console.error(err);
      setError('Something went wrong talking to the server.');
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;
    await sendMessage(input);
  };

  const handleKeyDown: React.KeyboardEventHandler<HTMLTextAreaElement> = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 px-6 py-4 flex items-center justify-between gap-4">
        <div>
          <h1 className="text-lg font-semibold tracking-tight">Chatbot</h1>
          <p className="text-xs text-slate-400">FastAPI + React + Tailwind starter</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="hidden sm:inline text-[11px] px-2 py-1 rounded-full bg-emerald-900/40 text-emerald-300 border border-emerald-700/60">
            Connected to backend (dev)
          </span>
          <div className="flex items-center gap-1 text-xs">
            <label htmlFor="locale" className="sr-only">
              Select language
            </label>
            <select
              id="locale"
              value={activeLocale}
              onChange={(e) => {
                const code = e.target.value as LocaleCode;
                setActiveLocale(code);
                setActiveCategoryId(null);
                setMessages([]);
                setLanguageWarning(null);
              }}
              className="bg-slate-900/70 border border-slate-700 rounded-lg text-xs px-2 py-1 text-slate-100 focus:outline-none focus:ring-1 focus:ring-sky-500"
            >
              {LOCALES.map((locale) => (
                <option key={locale.code} value={locale.code}>
                  {locale.flag} {locale.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </header>

      <main className="flex-1 flex flex-col max-w-3xl w-full mx-auto px-4 sm:px-6 py-6 gap-4">
        <section className="flex-1 overflow-y-auto rounded-xl border border-slate-800 bg-slate-900/40 p-4 space-y-3">
          {messages.length === 0 && (
            <div className="h-full flex items-center justify-center text-sm text-slate-500 text-center">
              <div>
                <p className="font-medium mb-2 text-slate-300 whitespace-pre-line">
                  {welcomeMessages[activeLocale]}
                </p>
              </div>
            </div>
          )}

          {messages.map((m) => (
            <div
              key={m.id}
              className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-3.5 py-2.5 text-sm shadow-sm border
                  ${m.role === 'user'
                    ? 'bg-sky-600 text-white border-sky-500'
                    : 'bg-slate-800 text-slate-50 border-slate-700'}
                `}
              >
                <p className="whitespace-pre-wrap break-words">{m.text}</p>
              </div>
            </div>
          ))}
        </section>

        <section className="space-y-4">
          <div className="flex flex-wrap gap-2 text-xs">
            {!activeCategoryId ? (
              CATEGORIES.map((cat) => (
                <button
                  key={cat.id}
                  type="button"
                  onClick={() => setActiveCategoryId(cat.id)}
                  className="px-4 py-2 rounded-xl border border-slate-700 bg-slate-900/70 text-slate-100 hover:bg-slate-800 hover:border-sky-500 hover:text-sky-100 transition-all flex items-center gap-2 shadow-sm"
                >
                  <span className="text-base">{cat.icon}</span>
                  <span className="font-medium">{cat.labels[activeLocale]}</span>
                </button>
              ))
            ) : (
              <>
                <button
                  type="button"
                  onClick={() => setActiveCategoryId(null)}
                  className="px-3 py-2 rounded-xl border border-slate-700 bg-slate-800/40 text-slate-400 hover:text-slate-200 transition-colors flex items-center gap-1"
                >
                  ← {activeLocale === 'tr' ? 'Geri' : activeLocale === 'ar' ? 'رجوع' : activeLocale === 'ru' ? 'Назад' : 'Back'}
                </button>
                {CATEGORIES.find((c) => c.id === activeCategoryId)?.questions[activeLocale].map((q, idx) => (
                  <button
                    key={`${activeCategoryId}-${idx}`}
                    type="button"
                    onClick={() => {
                      void sendMessage(q);
                    }}
                    className="px-4 py-2 rounded-xl border border-slate-700 bg-slate-900/70 text-slate-100 hover:bg-slate-800 hover:border-sky-500 hover:text-sky-100 transition-all shadow-sm"
                  >
                    {q}
                  </button>
                ))}
              </>
            )}
          </div>

          {error && (
            <p className="text-xs text-rose-400 bg-rose-950/50 border border-rose-800/70 rounded-md px-2.5 py-1.5">
              {error}
            </p>
          )}

          {languageWarning && (
            <div className="flex items-start gap-2 text-xs bg-amber-950/50 border border-amber-800/70 rounded-md px-2.5 py-1.5 text-amber-300">
              <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <span className="flex-1">{languageWarning}</span>
              <button
                onClick={() => setLanguageWarning(null)}
                className="text-amber-400 hover:text-amber-200 transition-colors"
                aria-label="Dismiss warning"
              >
                ✕
              </button>
            </div>
          )}

          <div className="flex items-end gap-2">
            <textarea
              className="flex-1 resize-none rounded-xl border border-slate-800 bg-slate-900/60 px-3 py-2 text-sm text-slate-100 shadow-sm focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500 placeholder:text-slate-500 min-h-[52px] max-h-32"
              rows={2}
              placeholder="Type your message and press Enter to send..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <button
              type="button"
              onClick={() => void handleSend()}
              disabled={loading || !input.trim()}
              className="inline-flex items-center justify-center rounded-xl bg-sky-600 text-sm font-medium text-white px-3.5 py-2 shadow-sm disabled:opacity-60 disabled:cursor-not-allowed hover:bg-sky-500 transition-colors border border-sky-500/70"
            >
              {loading ? 'Sending…' : 'Send'}
            </button>
          </div>

          <p className="text-[11px] text-slate-500 text-right">
            Enter to send • Shift+Enter for newline
          </p>
        </section>
      </main>
    </div>
  );
};

export default Chat;
