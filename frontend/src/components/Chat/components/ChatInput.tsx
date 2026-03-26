import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Send, Ban } from 'lucide-react';
import { LocaleCode } from '../../../config/chatConfig';

interface ChatInputProps {
  input: string;
  setInput: (val: string) => void;
  handleSend: () => void;
  handleKeyDown: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  loading: boolean;
  activeLocale: LocaleCode;
  inputFocused: boolean;
  setInputFocused: (val: boolean) => void;
  isBanned: boolean;
  banExpiresAt: number | null;
  onBanExpired: () => void;
}

const BAN_MESSAGES: Record<LocaleCode, string> = {
  en: 'Chat disabled due to inappropriate language',
  tr: 'Uygunsuz dil nedeniyle sohbet devre dışı',
  ar: 'تم تعطيل المحادثة بسبب لغة غير لائقة',
  ru: 'Чат отключён из-за ненормативной лексики',
};

const ChatInput: React.FC<ChatInputProps> = ({
  input,
  setInput,
  handleSend,
  handleKeyDown,
  loading,
  activeLocale,
  inputFocused,
  setInputFocused,
  isBanned,
  banExpiresAt,
  onBanExpired,
}) => {
  const [secondsLeft, setSecondsLeft] = useState<number>(0);

  // Live countdown — ticks every second while banned
  useEffect(() => {
    if (!isBanned || !banExpiresAt) return;

    const update = () => {
      const remaining = Math.ceil((banExpiresAt - Date.now()) / 1000);
      if (remaining <= 0) {
        onBanExpired();
      } else {
        setSecondsLeft(remaining);
      }
    };

    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, [isBanned, banExpiresAt, onBanExpired]);

  const placeholders: Record<LocaleCode, string> = {
    tr: 'Mesajınızı yazın...',
    ar: 'اكتب رسالتك...',
    ru: 'Введите сообщение...',
    en: 'Type your message...',
  };

  const minutes = Math.floor(secondsLeft / 60);
  const seconds = secondsLeft % 60;
  const countdownStr = `${minutes}:${String(seconds).padStart(2, '0')}`;

  const remainingLabel: Record<LocaleCode, string> = {
    en: `Remaining: ${countdownStr}`,
    tr: `Kalan süre: ${countdownStr}`,
    ar: `الوقت المتبقي: ${countdownStr}`,
    ru: `Осталось: ${countdownStr}`,
  };

  if (isBanned) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.97 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex items-center gap-3 rounded-xl border border-rose-700/60 bg-rose-950/40 px-4 py-3 shadow-[0_0_20px_-5px_rgba(239,68,68,0.2)]"
      >
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-rose-900/60 border border-rose-700/40 shrink-0">
          <Ban className="w-4 h-4 text-rose-400" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold text-rose-300">{BAN_MESSAGES[activeLocale]}</p>
          <p className="text-[10px] text-rose-500 mt-0.5">{remainingLabel[activeLocale]}</p>
        </div>
        <span className="text-lg font-bold text-rose-600 font-mono tabular-nums shrink-0">
          {countdownStr}
        </span>
      </motion.div>
    );
  }

  return (
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
        placeholder={placeholders[activeLocale] || placeholders.en}
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
  );
};

export default ChatInput;
