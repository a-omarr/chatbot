import React from 'react';
import Chat from './components/Chat';

const App: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-100">
      <div className="w-full max-w-4xl h-[600px]">
        <Chat />
      </div>
    </div>
  );
};

export default App;
