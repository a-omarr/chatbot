import React from 'react';
import { motion } from 'framer-motion';
import { Send } from 'lucide-react';
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
}

const ChatInput: React.FC<ChatInputProps> = ({
  input,
  setInput,
  handleSend,
  handleKeyDown,
  loading,
  activeLocale,
  inputFocused,
  setInputFocused,
}) => {
  const placeholders = {
    tr: 'Mesajınızı yazın...',
    ar: 'اكتب رسالتك...',
    ru: 'Введите сообщение...',
    en: 'Type your message...',
  };

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
