import React from 'react';
import { motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';
import { COMPANY_LOGO_URL, LocaleCode } from '../../../config/chatConfig';

interface WelcomeScreenProps {
  locale: LocaleCode;
  welcomeText: string;
}

const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ welcomeText }) => (
  <motion.div
    className="h-full flex flex-col items-center justify-center gap-6 px-4"
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    transition={{ duration: 0.6, delay: 0.2 }}
  >
    <motion.div
      className="relative"
      initial={{ scale: 0.5, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 200, damping: 20, delay: 0.3 }}
    >
      <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700/50 p-3 flex items-center justify-center shadow-lg animate-glow-pulse">
        <img src={COMPANY_LOGO_URL} alt="Toros Yazılım" className="w-full h-full object-contain" />
      </div>
      <motion.div
        className="absolute inset-0 -m-2 rounded-3xl border border-sky-500/20"
        animate={{ scale: [1, 1.1, 1], opacity: [0.3, 0.6, 0.3] }}
        transition={{ repeat: Infinity, duration: 3, ease: 'easeInOut' }}
      />
    </motion.div>

    <motion.div
      className="text-center max-w-md"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5, duration: 0.5 }}
    >
      <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-line font-medium">{welcomeText}</p>
    </motion.div>

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

export default WelcomeScreen;
