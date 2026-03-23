import React from 'react';
import { motion } from 'framer-motion';
import { COMPANY_LOGO_URL } from '../../../config/chatConfig';

interface TypingIndicatorProps {
  status: string;
}

const TypingIndicator: React.FC<TypingIndicatorProps> = ({ status }) => (
  <motion.div
    className="flex items-center gap-3"
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -5 }}
    transition={{ duration: 0.3 }}
  >
    <motion.div
      className="flex-shrink-0"
      animate={{ scale: [1, 1.05, 1] }}
      transition={{ repeat: Infinity, duration: 2, ease: 'easeInOut' }}
    >
      <div className="w-8 h-8 rounded-full bg-slate-800/80 border border-sky-500/30 p-1 flex items-center justify-center overflow-hidden shadow-[0_0_15px_rgba(56,189,248,0.2)]">
        <img src={COMPANY_LOGO_URL} alt="Bot" className="w-full h-full object-contain opacity-70" />
      </div>
    </motion.div>

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

export default TypingIndicator;
