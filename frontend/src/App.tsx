import React from 'react';
import { motion } from 'framer-motion';
import Chat from './components/Chat';

const App: React.FC = () => {
  return (
    <div className="relative min-h-screen flex items-center justify-center bg-slate-950 text-slate-100 overflow-hidden">
      {/* Animated background orbs */}
      <div className="bg-orb bg-orb-1" />
      <div className="bg-orb bg-orb-2" />
      <div className="bg-orb bg-orb-3" />

      {/* Main chat container */}
      <motion.div
        className="relative z-10 w-full max-w-4xl h-[92vh] sm:h-[88vh] md:h-[85vh] mx-2 sm:mx-4"
        initial={{ opacity: 0, y: 30, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
      >
        <Chat />
      </motion.div>
    </div>
  );
};

export default App;
