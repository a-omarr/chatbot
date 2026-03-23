import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft } from 'lucide-react';
import { CATEGORIES, LocaleCode } from '../../../config/chatConfig';

interface CategoryPillsProps {
  activeLocale: LocaleCode;
  activeCategoryId: string | null;
  setActiveCategoryId: (id: string | null) => void;
  sendMessage: (text: string) => void;
  containerVariants: any;
  itemVariants: any;
}

const CategoryPills: React.FC<CategoryPillsProps> = ({
  activeLocale,
  activeCategoryId,
  setActiveCategoryId,
  sendMessage,
  containerVariants,
  itemVariants,
}) => {
  return (
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
  );
};

export default CategoryPills;
