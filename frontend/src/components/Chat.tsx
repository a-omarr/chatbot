import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, ArrowLeft, ExternalLink, Sparkles } from 'lucide-react';

/* ─── Types ────────────────────────────────────────────── */
export interface Message {
  id: number;
  role: 'user' | 'bot';
  text: string;
  resourceUrl?: string;
}

interface ChatApiResponse {
  reply: string;
  language?: string | null;
  suggestions?: string[] | null;
  language_warning?: string | null;
  is_mismatch?: boolean;
  suggested_language?: LocaleCode | null;
  resource_url?: string;
}

interface ChatProps {
  apiUrl?: string;
}

/* ─── Constants ────────────────────────────────────────── */
const DEFAULT_API_URL = '/api/v1/bot/chat';
const COMPANY_LOGO_URL = 'https://www.torosyazilim.com.tr/images/toros-yazilim-normal.svg';

type LocaleCode = 'en' | 'tr' | 'ar' | 'ru';

interface LocaleConfig {
  code: LocaleCode;
  label: string;
  flag: string;
  suggestions: string[];
}

const LOCALES: LocaleConfig[] = [
  { code: 'en', label: 'English', flag: '🇬🇧', suggestions: [] },
  { code: 'tr', label: 'Türkçe', flag: '🇹🇷', suggestions: [] },
  { code: 'ar', label: 'العربية', flag: '🇸🇦', suggestions: [] },
  { code: 'ru', label: 'Русский', flag: '🇷🇺', suggestions: [] },
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
      en: ['What is Makscyber SIEM?', 'What does AuthNAC do?', 'Do you offer identity management solutions?', 'How can I improve my company\'s cybersecurity?', 'Can I request a demo for your security products?'],
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

const findLocale = (code: LocaleCode): LocaleConfig =>
  LOCALES.find((l) => l.code === code) ?? LOCALES[0];

/* ─── Animation Variants ──────────────────────────────── */
const messageVariants = {
  hidden: (role: string) => ({
    opacity: 0,
    x: role === 'user' ? 30 : -30,
    y: 10,
    scale: 0.95,
  }),
  visible: {
    opacity: 1,
    x: 0,
    y: 0,
    scale: 1,
    transition: { type: 'spring' as const, stiffness: 300, damping: 30, mass: 0.8 },
  },
  exit: {
    opacity: 0,
    scale: 0.9,
    transition: { duration: 0.15 },
  },
};

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.06, delayChildren: 0.1 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 12, scale: 0.95 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { type: 'spring' as const, stiffness: 400, damping: 25 },
  },
};

/* ─── Typing Indicator Component ──────────────────────── */
const TypingIndicator: React.FC<{ status: string }> = ({ status }) => (
  <motion.div
    className="flex items-center gap-3"
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -5 }}
    transition={{ duration: 0.3 }}
  >
    {/* Bot avatar */}
    <motion.div
      className="flex-shrink-0"
      animate={{ scale: [1, 1.05, 1] }}
      transition={{ repeat: Infinity, duration: 2, ease: 'easeInOut' }}
    >
      <div className="w-8 h-8 rounded-full bg-slate-800/80 border border-sky-500/30 p-1 flex items-center justify-center overflow-hidden shadow-[0_0_15px_rgba(56,189,248,0.2)]">
        <img src={COMPANY_LOGO_URL} alt="Bot" className="w-full h-full object-contain opacity-70" />
      </div>
    </motion.div>

    {/* Dots + status */}
    <div className="flex items-center gap-2.5 bg-slate-800/40 border border-slate-700/50 rounded-2xl px-4 py-2.5">
      <div className="flex items-center gap-1">
        {[0, 1, 2].map((i) => (
          <motion.span
            key={i}
            className="typing-dot"
            animate={{ y: [0, -6, 0] }}
            transition={{
              repeat: Infinity,
              duration: 0.6,
              delay: i * 0.15,
              ease: 'easeInOut',
            }}
          />
        ))}
      </div>
      <span className="text-xs text-slate-400 italic">{status}</span>
    </div>
  </motion.div>
);

/* ─── Welcome Screen Component ────────────────────────── */
const WelcomeScreen: React.FC<{ locale: LocaleCode; welcomeText: string }> = ({ welcomeText }) => (
  <motion.div
    className="h-full flex flex-col items-center justify-center gap-6 px-4"
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    transition={{ duration: 0.6, delay: 0.2 }}
  >
    {/* Animated logo */}
    <motion.div
      className="relative"
      initial={{ scale: 0.5, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 200, damping: 20, delay: 0.3 }}
    >
      <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700/50 p-3 flex items-center justify-center shadow-lg animate-glow-pulse">
        <img src={COMPANY_LOGO_URL} alt="Toros Yazılım" className="w-full h-full object-contain" />
      </div>
      {/* Glow ring behind logo */}
      <motion.div
        className="absolute inset-0 -m-2 rounded-3xl border border-sky-500/20"
        animate={{ scale: [1, 1.1, 1], opacity: [0.3, 0.6, 0.3] }}
        transition={{ repeat: Infinity, duration: 3, ease: 'easeInOut' }}
      />
    </motion.div>

    {/* Welcome text */}
    <motion.div
      className="text-center max-w-md"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5, duration: 0.5 }}
    >
      <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-line font-medium">{welcomeText}</p>
    </motion.div>

    {/* Sparkle hint */}
    <motion.div
      className="flex items-center gap-2 text-xs text-slate-500"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.8 }}
    >
      <Sparkles className="w-3.5 h-3.5 text-sky-400/60" />
      <span>AI-powered assistant</span>
    </motion.div>
  </motion.div>
);

/* ─── Main Chat Component ─────────────────────────────── */
const Chat: React.FC<ChatProps> = ({ apiUrl = DEFAULT_API_URL }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [thinkingStatus, setThinkingStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeLocale, setActiveLocale] = useState<LocaleCode>('en');
  const [activeCategoryId, setActiveCategoryId] = useState<string | null>(null);
  const [languageWarning, setLanguageWarning] = useState<string | null>(null);
  const [suggestedLanguage, setSuggestedLanguage] = useState<LocaleCode | null>(null);
  const [inputFocused, setInputFocused] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLElement>(null);

  const welcomeMessages: Record<LocaleCode, string> = {
    en: '👋 Welcome to Toros Yazılım.\nHow can we assist you today?\nChoose a topic below or type your question.',
    tr: '👋 Toros Yazılım\'a hoş geldiniz.\nSize bugün nasıl yardımcı olabiliriz?\nAşağıdan bir konu seçin veya sorunuzu yazın.',
    ar: '👋 مرحبًا بكم في توروس يازليم.\nكيف يمكننا مساعدتكم اليوم؟\nاختاروا موضوعًا أدناه أو اكتبوا سؤالكم.',
    ru: '👋 Добро пожаловать в Toros Yazılım.\nЧем мы можем вам помочь сегодня?\nВыберите тему ниже или напишите свой вопрос.',
  };

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, thinkingStatus]);

  const sendMessage = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    setError(null);
    const userMessage: Message = { id: Date.now(), role: 'user', text: trimmed };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    const statuses = {
      en: ['Analyzing...', 'Generating response...'],
      tr: ['Analiz ediliyor...', 'Yanıt oluşturuluyor...'],
      ar: ['جاري التحليل...', 'جاري إنشاء الرد...'],
      ru: ['Анализ...', 'Генерация ответа...'],
    };

    const currentStatuses = statuses[activeLocale] || statuses.en;

    try {
      setThinkingStatus(currentStatuses[0]);

      const resPromise = fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed, language: activeLocale }),
      });

      await new Promise((r) => setTimeout(r, 1000));
      setThinkingStatus(currentStatuses[1]);
      await new Promise((r) => setTimeout(r, 800));

      const res = await resPromise;
      if (!res.ok) throw new Error(`Request failed with status ${res.status}`);

      const data: ChatApiResponse = await res.json();

      if (data.reply) {
        const botMessage: Message = {
          id: Date.now() + 1,
          role: 'bot',
          text: data.reply,
          resourceUrl: data.resource_url || undefined,
        };
        setMessages((prev) => [...prev, botMessage]);
      }

      if (data.language_warning) {
        setLanguageWarning(data.language_warning);
        setSuggestedLanguage(data.suggested_language || null);
      } else {
        setLanguageWarning(null);
        setSuggestedLanguage(null);
      }
    } catch (err) {
      console.error(err);
      setError('Something went wrong talking to the server.');
    } finally {
      setLoading(false);
      setThinkingStatus(null);
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
    <div className="flex flex-col h-full rounded-2xl overflow-hidden glass shadow-2xl shadow-sky-950/20">
      {/* ─── Header ────────────────────────────────── */}
      <motion.header
        className="glass-header gradient-border px-5 py-3.5 flex items-center justify-between gap-4"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1 }}
      >
        <div className="flex items-center gap-3">
          {/* Animated avatar */}
          <motion.div
            className="relative"
            whileHover={{ scale: 1.05 }}
            transition={{ type: 'spring', stiffness: 400 }}
          >
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700/50 p-1.5 flex items-center justify-center overflow-hidden">
              <img src={COMPANY_LOGO_URL} alt="Toros" className="w-full h-full object-contain" />
            </div>
            {/* Online indicator */}
            <motion.div
              className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-emerald-400 border-2 border-slate-900"
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ repeat: Infinity, duration: 2, ease: 'easeInOut' }}
            />
          </motion.div>

          <div>
            <h1 className="text-sm font-semibold tracking-tight bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
              Toros AI Assistant
            </h1>
            <p className="text-[10px] text-emerald-400/80 font-medium flex items-center gap-1">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Online
            </p>
          </div>
        </div>

        {/* Language selector */}
        <motion.div
          className="flex items-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <label htmlFor="locale" className="sr-only">Select language</label>
          <select
            id="locale"
            value={activeLocale}
            onChange={(e) => {
              const code = e.target.value as LocaleCode;
              setActiveLocale(code);
              setActiveCategoryId(null);
              setMessages([]);
              setLanguageWarning(null);
              setSuggestedLanguage(null);
            }}
            className="bg-slate-800/50 border border-slate-700/50 rounded-lg text-xs px-2.5 py-1.5 text-slate-200 focus:outline-none focus:ring-1 focus:ring-sky-500/50 hover:bg-slate-700/50 transition-all cursor-pointer appearance-none pr-7"
            style={{
              backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e")`,
              backgroundPosition: 'right 0.35rem center',
              backgroundRepeat: 'no-repeat',
              backgroundSize: '1.2em 1.2em',
            }}
          >
            {LOCALES.map((locale) => (
              <option key={locale.code} value={locale.code}>
                {locale.flag} {locale.label}
              </option>
            ))}
          </select>
        </motion.div>
      </motion.header>

      {/* ─── Messages ──────────────────────────────── */}
      <section
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-3"
      >
        {messages.length === 0 ? (
          <WelcomeScreen locale={activeLocale} welcomeText={welcomeMessages[activeLocale]} />
        ) : (
          <AnimatePresence mode="popLayout">
            {messages.map((m) => (
              <motion.div
                key={m.id}
                custom={m.role}
                variants={messageVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                layout
                className={`flex items-start gap-3 ${m.role === 'user' ? 'justify-end flex-row-reverse' : 'justify-start'}`}
              >
                {/* Bot avatar */}
                {m.role === 'bot' && (
                  <motion.div
                    className="flex-shrink-0 mt-0.5"
                    initial={{ scale: 0, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ type: 'spring', stiffness: 400, damping: 20, delay: 0.1 }}
                  >
                    <div className="w-8 h-8 rounded-full bg-slate-800/80 border border-sky-500/20 p-1 flex items-center justify-center shadow-lg overflow-hidden">
                      <img src={COMPANY_LOGO_URL} alt="Bot" className="w-full h-full object-contain" />
                    </div>
                  </motion.div>
                )}

                {/* Message bubble */}
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm shadow-md
                    ${m.role === 'user'
                      ? 'bg-gradient-to-br from-sky-600 to-blue-700 text-white border border-sky-500/30'
                      : 'bg-slate-800/60 text-slate-50 border border-slate-700/40 msg-shimmer'
                    }`}
                >
                  <p className="whitespace-pre-wrap break-words relative z-10 leading-relaxed">{m.text}</p>
                  {m.resourceUrl && (
                    <motion.div
                      className="mt-2.5 pt-2 border-t border-slate-600/30 relative z-10"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.3 }}
                    >
                      <a
                        href={m.resourceUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-sky-400 hover:text-sky-300 transition-colors group"
                      >
                        <ExternalLink className="w-3 h-3 group-hover:rotate-12 transition-transform" />
                        {activeLocale === 'tr' ? '[Kaynak]' : activeLocale === 'ar' ? '[المصدر]' : activeLocale === 'ru' ? '[Источник]' : '[Source]'}
                      </a>
                    </motion.div>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        )}

        {/* Typing indicator */}
        <AnimatePresence>
          {thinkingStatus && <TypingIndicator status={thinkingStatus} />}
        </AnimatePresence>

        <div ref={messagesEndRef} />
      </section>

      {/* ─── Bottom Section ────────────────────────── */}
      <section className="border-t border-slate-800/50 p-4 sm:p-5 space-y-3 bg-slate-950/40 backdrop-blur-sm">
        {/* Category pills */}
        <div className="flex flex-wrap gap-2 text-xs">
          <AnimatePresence mode="wait">
            {!activeCategoryId ? (
              <motion.div
                key="categories"
                className="flex flex-wrap gap-2"
                variants={containerVariants}
                initial="hidden"
                animate="visible"
                exit={{ opacity: 0, transition: { duration: 0.15 } }}
              >
                {CATEGORIES.map((cat) => (
                  <motion.button
                    key={cat.id}
                    variants={itemVariants}
                    type="button"
                    onClick={() => setActiveCategoryId(cat.id)}
                    className="px-3.5 py-2 rounded-xl border border-slate-700/50 bg-slate-800/40 text-slate-200 hover:bg-slate-700/50 hover:border-sky-500/40 hover:text-sky-100 transition-all flex items-center gap-2 btn-glow"
                    whileHover={{ scale: 1.03, y: -1 }}
                    whileTap={{ scale: 0.97 }}
                  >
                    <span className="text-base">{cat.icon}</span>
                    <span className="font-medium">{cat.labels[activeLocale]}</span>
                  </motion.button>
                ))}
              </motion.div>
            ) : (
              <motion.div
                key="questions"
                className="flex flex-wrap gap-2"
                variants={containerVariants}
                initial="hidden"
                animate="visible"
                exit={{ opacity: 0, transition: { duration: 0.15 } }}
              >
                <motion.button
                  variants={itemVariants}
                  type="button"
                  onClick={() => setActiveCategoryId(null)}
                  className="px-3 py-2 rounded-xl border border-slate-700/50 bg-slate-800/30 text-slate-400 hover:text-slate-200 transition-colors flex items-center gap-1.5 btn-glow"
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.97 }}
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  {activeLocale === 'tr' ? 'Geri' : activeLocale === 'ar' ? 'رجوع' : activeLocale === 'ru' ? 'Назад' : 'Back'}
                </motion.button>
                {CATEGORIES.find((c) => c.id === activeCategoryId)?.questions[activeLocale].map((q, idx) => (
                  <motion.button
                    key={`${activeCategoryId}-${idx}`}
                    variants={itemVariants}
                    type="button"
                    onClick={() => void sendMessage(q)}
                    className="px-3.5 py-2 rounded-xl border border-slate-700/50 bg-slate-800/40 text-slate-200 hover:bg-slate-700/50 hover:border-sky-500/40 hover:text-sky-100 transition-all btn-glow"
                    whileHover={{ scale: 1.03, y: -1 }}
                    whileTap={{ scale: 0.97 }}
                  >
                    {q}
                  </motion.button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Error message */}
        <AnimatePresence>
          {error && (
            <motion.p
              className="text-xs text-rose-400 bg-rose-950/50 border border-rose-800/50 rounded-xl px-3 py-2"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
            >
              {error}
            </motion.p>
          )}
        </AnimatePresence>

        {/* Language warning */}
        <AnimatePresence>
          {languageWarning && (
            <motion.div
              className="flex items-center gap-3 text-xs bg-rose-950/30 border border-rose-800/40 rounded-xl px-4 py-3 text-rose-200"
              initial={{ opacity: 0, y: 10, height: 0 }}
              animate={{ opacity: 1, y: 0, height: 'auto' }}
              exit={{ opacity: 0, y: -5, height: 0 }}
              transition={{ type: 'spring', stiffness: 300, damping: 25 }}
            >
              <div className="bg-rose-900/40 p-1.5 rounded-lg border border-rose-700/30">
                <svg className="w-4 h-4 text-rose-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <span className="flex-1 font-medium">{languageWarning}</span>
              {suggestedLanguage && (
                <motion.button
                  type="button"
                  onClick={() => {
                    setActiveLocale(suggestedLanguage);
                    setMessages([]);
                    setActiveCategoryId(null);
                    setLanguageWarning(null);
                    setSuggestedLanguage(null);
                  }}
                  className="px-3 py-1.5 rounded-lg bg-rose-600/80 hover:bg-rose-500 text-white font-semibold transition-all shadow-sm flex items-center gap-1.5 whitespace-nowrap"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <span className="text-sm">{findLocale(suggestedLanguage).flag}</span>
                  {findLocale(suggestedLanguage).label}
                </motion.button>
              )}
              <button
                onClick={() => {
                  setLanguageWarning(null);
                  setSuggestedLanguage(null);
                }}
                className="p-1 px-2 text-rose-400 hover:text-rose-200 transition-colors rounded-lg hover:bg-rose-900/30"
                aria-label="Dismiss warning"
              >
                ✕
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Input area */}
        <div className={`flex items-end gap-2.5 rounded-xl border transition-all duration-300 p-1
          ${inputFocused
            ? 'border-sky-500/40 shadow-[0_0_20px_-5px_rgba(56,189,248,0.15)]'
            : 'border-slate-800/60'
          }
          bg-slate-900/40`}
        >
          <textarea
            className="flex-1 resize-none bg-transparent px-3 py-2.5 text-sm text-slate-100 focus:outline-none placeholder:text-slate-500/70 min-h-[44px] max-h-28"
            rows={1}
            placeholder={
              activeLocale === 'tr' ? 'Mesajınızı yazın...' :
                activeLocale === 'ar' ? 'اكتب رسالتك...' :
                  activeLocale === 'ru' ? 'Введите сообщение...' :
                    'Type your message...'
            }
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setInputFocused(true)}
            onBlur={() => setInputFocused(false)}
          />
          <motion.button
            type="button"
            onClick={() => void handleSend()}
            disabled={loading || !input.trim()}
            className="send-btn rounded-lg text-white p-2.5 m-0.5 flex items-center justify-center disabled:opacity-30"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.9 }}
          >
            <Send className="w-4 h-4 relative z-10" />
          </motion.button>
        </div>

        {/* Hint */}
        <p className="text-[10px] text-slate-600 text-center">
          ↵ Enter to send • Shift+↵ for newline
        </p>
      </section>
    </div>
  );
};

export default Chat;
