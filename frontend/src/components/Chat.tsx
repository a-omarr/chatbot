import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  LocaleCode, 
  LOCALES, 
  welcomeMessages, 
  COMPANY_LOGO_URL, 
  DEFAULT_API_URL 
} from '../config/chatConfig';

const BAN_DURATION_MS = 5 * 60 * 1000; // 5 minutes
const BAN_STORAGE_KEY = 'chat_ban_expires_at';

function getStoredBanExpiry(): number | null {
  try {
    const val = localStorage.getItem(BAN_STORAGE_KEY);
    if (!val) return null;
    const ts = parseInt(val, 10);
    return ts > Date.now() ? ts : null;
  } catch {
    return null;
  }
}

function storeBanExpiry(expiry: number): void {
  try { localStorage.setItem(BAN_STORAGE_KEY, String(expiry)); } catch {}
}

function clearBanExpiry(): void {
  try { localStorage.removeItem(BAN_STORAGE_KEY); } catch {}
}

import TypingIndicator from './Chat/components/TypingIndicator';
import WelcomeScreen from './Chat/components/WelcomeScreen';
import MessageBubble from './Chat/components/MessageBubble';
import CategoryPills from './Chat/components/CategoryPills';
import ChatInput from './Chat/components/ChatInput';

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
  is_banned?: boolean;
}

interface ChatProps {
  apiUrl?: string;
}

/* ─── Helpers ────────────────────────────────────────── */
const findLocale = (code: LocaleCode) =>
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

  // Ban state — initialised from localStorage so it survives page refresh
  const [banExpiresAt, setBanExpiresAt] = useState<number | null>(() => getStoredBanExpiry());
  const isBanned = banExpiresAt !== null && banExpiresAt > Date.now();

  const handleBanExpired = useCallback(() => {
    setBanExpiresAt(null);
    clearBanExpiry();
  }, []);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, thinkingStatus]);

  const sendMessage = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || loading || isBanned) return;

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

      // Handle ban — persist expiry in localStorage for 5 minutes
      if (data.is_banned) {
        const expiry = Date.now() + BAN_DURATION_MS;
        setBanExpiresAt(expiry);
        storeBanExpiry(expiry);
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

  const handleSend = () => {
    if (!input.trim()) return;
    void sendMessage(input);
  };

  const handleKeyDown: React.KeyboardEventHandler<HTMLTextAreaElement> = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
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
          <motion.div
            className="relative"
            whileHover={{ scale: 1.05 }}
            transition={{ type: 'spring', stiffness: 400 }}
          >
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700/50 p-1.5 flex items-center justify-center overflow-hidden">
              <img src={COMPANY_LOGO_URL} alt="Toros" className="w-full h-full object-contain" />
            </div>
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
              <MessageBubble 
                key={m.id} 
                message={m} 
                locale={activeLocale} 
                variants={messageVariants} 
              />
            ))}
          </AnimatePresence>
        )}

        <AnimatePresence>
          {thinkingStatus && <TypingIndicator status={thinkingStatus} />}
        </AnimatePresence>

        <div ref={messagesEndRef} />
      </section>

      {/* ─── Bottom Section ────────────────────────── */}
      <section className="border-t border-slate-800/50 p-4 sm:p-5 space-y-3 bg-slate-950/40 backdrop-blur-sm">
        <CategoryPills 
          activeLocale={activeLocale}
          activeCategoryId={activeCategoryId}
          setActiveCategoryId={setActiveCategoryId}
          sendMessage={sendMessage}
          containerVariants={containerVariants}
          itemVariants={itemVariants}
          isBanned={isBanned}
        />

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

        <ChatInput 
          input={input}
          setInput={setInput}
          handleSend={handleSend}
          handleKeyDown={handleKeyDown}
          loading={loading}
          activeLocale={activeLocale}
          inputFocused={inputFocused}
          setInputFocused={setInputFocused}
          isBanned={isBanned}
          banExpiresAt={banExpiresAt}
          onBanExpired={handleBanExpired}
        />

        <p className="text-[10px] text-slate-600 text-center">
          ↵ Enter to send • Shift+↵ for newline
        </p>
      </section>
    </div>
  );
};

export default Chat;
