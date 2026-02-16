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
    suggestions: [
      'Who is Toros Yazilim?',
      'Tell me about KIYOS',
      'What services do you offer?',
      'Does KIYOS support LDAP?',
      'How can I contact you?',
    ],
  },
  {
    code: 'tr',
    label: 'Türkçe',
    flag: '🇹🇷',
    suggestions: [
      'Toros Yazilim kimdir?',
      'KIYOS nedir?',
      'Hizmetleriniz neler?',
      'KIYOS LDAP destekliyor mu?',
      'Size nasıl ulaşabilirim?',
    ],
  },
  {
    code: 'ar',
    label: 'العربية',
    flag: '🇸🇦',
    suggestions: [
      'من هي توروس يازليم؟',
      'أخبرني عن KIYOS',
      'ما هي خدماتكم؟',
      'هل يدعم KIYOS نظام LDAP؟',
      'كيف يمكنني الاتصال بكم؟',
    ],
  },
  {
    code: 'ru',
    label: 'Русский',
    flag: '🇷🇺',
    suggestions: [
      'Кто такая Toros Yazilim?',
      'Расскажите о KIYOS',
      'Какие услуги вы предлагаете?',
      'Поддерживает ли KIYOS LDAP?',
      'Как с вами связаться?',
    ],
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
  const [suggestions, setSuggestions] = useState<string[]>(findLocale('en').suggestions);
  const [usedSuggestions, setUsedSuggestions] = useState<string[]>([]);
  const [languageWarning, setLanguageWarning] = useState<string | null>(null);

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

      if (data.suggestions && Array.isArray(data.suggestions)) {
        // Filter out any suggestions that have already been used based on the new usedSuggestions state
        const newUsed = [...usedSuggestions, trimmed];
        setUsedSuggestions(newUsed);
        setSuggestions(data.suggestions.filter((s) => !newUsed.includes(s)));
      }

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
                const locale = findLocale(code);
                // Reset used suggestions on language change so the new language list starts fresh (or persistent if preferred, but fresh makes sense for new context)
                setUsedSuggestions([]);
                setSuggestions(locale.suggestions);
                setMessages([]);
                // Clear language warning when switching languages
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
                <p className="font-medium mb-1">Start the conversation</p>
                <p>Ask the bot anything to see a reply here.</p>
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

        <section className="space-y-2">
          {suggestions.length > 0 && (
            <div className="flex flex-wrap gap-2 text-xs">
              {suggestions.map((s, idx) => (
                <button
                  key={`${s}-${idx}`}
                  type="button"
                  onClick={() => {
                    void sendMessage(s);
                  }}
                  className="px-3 py-1 rounded-full border border-slate-700 bg-slate-900/70 text-slate-100 hover:bg-slate-800 hover:border-sky-500 hover:text-sky-100 transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          )}

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
