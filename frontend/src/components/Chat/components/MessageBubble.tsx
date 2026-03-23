import React from 'react';
import { motion } from 'framer-motion';
import { ExternalLink } from 'lucide-react';
import { COMPANY_LOGO_URL, LocaleCode } from '../../../config/chatConfig';
import { Message } from '../../Chat';

interface MessageBubbleProps {
  message: Message;
  locale: LocaleCode;
  variants: any;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, locale, variants }) => (
  <motion.div
    custom={message.role}
    variants={variants}
    initial="hidden"
    animate="visible"
    exit="exit"
    layout
    className={`flex items-start gap-3 ${message.role === 'user' ? 'justify-end flex-row-reverse' : 'justify-start'}`}
  >
    {message.role === 'bot' && (
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

    <div
      className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm shadow-md
        ${message.role === 'user'
          ? 'bg-gradient-to-br from-sky-600 to-blue-700 text-white border border-sky-500/30'
          : 'bg-slate-800/60 text-slate-50 border border-slate-700/40 msg-shimmer'
        }`}
    >
      <p className="whitespace-pre-wrap break-words relative z-10 leading-relaxed">{message.text}</p>
      {message.resourceUrl && (
        <motion.div
          className="mt-2.5 pt-2 border-t border-slate-600/30 relative z-10"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <a
            href={message.resourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-sky-400 hover:text-sky-300 transition-colors group"
          >
            <ExternalLink className="w-3 h-3 group-hover:rotate-12 transition-transform" />
            {locale === 'tr' ? '[Kaynak]' : locale === 'ar' ? '[المصدر]' : locale === 'ru' ? '[Источник]' : '[Source]'}
          </a>
        </motion.div>
      )}
    </div>
  </motion.div>
);

export default MessageBubble;
