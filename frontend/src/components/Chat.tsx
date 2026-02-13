import React, { useState } from 'react';

export interface Message {
  id: number;
  role: 'user' | 'bot';
  text: string;
}

interface ChatProps {
  /** Optional override for the API URL. Defaults to FastAPI v1 bot endpoint. */
  apiUrl?: string;
}

const DEFAULT_API_URL = '/api/v1/bot/chat';

const Chat: React.FC<ChatProps> = ({ apiUrl = DEFAULT_API_URL }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSend = async () => {
    const trimmed = input.trim();
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
        body: JSON.stringify({ message: trimmed }),
      });

      if (!res.ok) {
        throw new Error(`Request failed with status ${res.status}`);
      }

      const data: { reply: string } = await res.json();

      const botMessage: Message = {
        id: Date.now() + 1,
        role: 'bot',
        text: data.reply,
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      console.error(err);
      setError('Something went wrong talking to the server.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown: React.KeyboardEventHandler<HTMLTextAreaElement> = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold tracking-tight">Chatbot</h1>
          <p className="text-xs text-slate-400">FastAPI + React + Tailwind starter</p>
        </div>
        <span className="text-[11px] px-2 py-1 rounded-full bg-emerald-900/40 text-emerald-300 border border-emerald-700/60">
          Connected to backend (dev)
        </span>
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
          {error && (
            <p className="text-xs text-rose-400 bg-rose-950/50 border border-rose-800/70 rounded-md px-2.5 py-1.5">
              {error}
            </p>
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
