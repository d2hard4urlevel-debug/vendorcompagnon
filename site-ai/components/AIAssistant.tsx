'use client';

import { useState } from 'react';

type Message = {
  role: 'user' | 'assistant';
  content: string;
};

const startMessage: Message = {
  role: 'assistant',
  content: 'Bonjour, je vais vous aider à trouver le bon moteur. Quelle est l’année, la marque et le modèle du véhicule?',
};

export default function AIAssistant() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([startMessage]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<'openai' | 'fallback' | 'error' | 'idle'>('idle');

  async function sendMessage(event?: React.FormEvent) {
    event?.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    const nextMessages: Message[] = [...messages, { role: 'user', content: text }];
    setMessages(nextMessages);
    setInput('');
    setLoading(true);
    setOpen(true);

    try {
      const response = await fetch('/api/assistant', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: nextMessages }),
      });
      const data = await response.json();
      setMessages([...nextMessages, { role: 'assistant', content: data.reply }]);
      setMode(data.mode || 'openai');
    } catch (error) {
      setMessages([
        ...nextMessages,
        { role: 'assistant', content: 'Désolé, l’assistant ne répond pas. Donnez-moi l’année, le modèle, le moteur et le VIN pour préparer la demande.' },
      ]);
      setMode('error');
    } finally {
      setLoading(false);
    }
  }

  function resetChat() {
    setMessages([startMessage]);
    setInput('');
    setMode('idle');
    setOpen(false);
  }

  return (
    <div className="grid overflow-hidden rounded-[2rem] border border-white/10 bg-[#101010] lg:grid-cols-[0.9fr_1.1fr]">
      <div className="border-b border-white/10 p-7 lg:border-b-0 lg:border-r">
        <p className="text-sm uppercase tracking-[0.3em] text-orange-400">Assistant IA</p>
        <h2 className="mt-3 text-4xl font-black leading-tight">Un vendeur IA qui qualifie le client.</h2>
        <p className="mt-4 leading-7 text-white/58">Il pose les bonnes questions : année, modèle, moteur, VIN, ville, installation et budget. Il ne donne pas de prix inventé.</p>
        <div className="mt-7 flex flex-wrap gap-3">
          <button onClick={() => setOpen(true)} className="rounded-2xl bg-orange-500 px-6 py-4 font-black text-black transition hover:bg-orange-400">Démarrer l’assistant</button>
          <button onClick={resetChat} className="rounded-2xl border border-white/10 px-6 py-4 font-bold text-white/65 transition hover:bg-white/5">Reset</button>
        </div>
        <div className="mt-5 rounded-2xl border border-white/10 bg-black/30 p-4 text-sm text-white/45">
          Mode : {mode === 'openai' ? 'IA connectée' : mode === 'fallback' ? 'Test sans clé API' : mode === 'error' ? 'Erreur API' : 'Prêt'}
        </div>
      </div>

      <div className="bg-black/35 p-7">
        <div className="rounded-3xl border border-white/10 bg-[#070707] p-5">
          <div className="mb-5 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-full bg-orange-500 text-xl font-black text-black">AI</div>
              <div>
                <div className="font-black">Agent moteur</div>
                <div className="text-xs text-white/40">Qualification intelligente</div>
              </div>
            </div>
            <div className="rounded-full border border-white/10 px-3 py-1 text-xs text-white/50">Chat</div>
          </div>

          <div className="max-h-[420px] space-y-3 overflow-y-auto pr-1">
            {messages.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                className={message.role === 'assistant'
                  ? 'max-w-[88%] rounded-2xl bg-white/10 p-4 text-sm leading-6 text-white/75'
                  : 'ml-auto max-w-[88%] rounded-2xl bg-orange-500 p-4 text-sm font-bold leading-6 text-black'}
              >
                {message.content}
              </div>
            ))}
            {loading && <div className="max-w-[88%] rounded-2xl bg-white/10 p-4 text-sm text-white/50">L’assistant réfléchit...</div>}
          </div>

          {open ? (
            <form onSubmit={sendMessage} className="mt-6 flex gap-3">
              <input
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="Répondre au vendeur IA..."
                className="min-w-0 flex-1 rounded-2xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white outline-none placeholder:text-white/30 focus:border-orange-500"
              />
              <button disabled={loading} className="rounded-2xl bg-white px-5 py-3 text-sm font-black text-black disabled:opacity-50">Envoyer</button>
            </form>
          ) : (
            <div className="mt-6 rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm text-white/45">Cliquez sur Démarrer pour tester l’assistant.</div>
          )}
        </div>
      </div>
    </div>
  );
}
