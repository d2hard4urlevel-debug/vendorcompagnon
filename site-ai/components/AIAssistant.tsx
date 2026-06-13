'use client';

import { useState } from 'react';

const questions = [
  'Quel est l’année, la marque et le modèle du véhicule?',
  'Quel moteur recherchez-vous exactement?',
  'Avez-vous le VIN ou le 8e caractère du VIN?',
  'Dans quelle ville doit-on livrer?',
  'Voulez-vous le moteur seulement ou l’installation aussi?',
];

export default function AIAssistant() {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(0);

  return (
    <div className="grid overflow-hidden rounded-[2rem] border border-white/10 bg-[#101010] lg:grid-cols-[0.9fr_1.1fr]">
      <div className="border-b border-white/10 p-7 lg:border-b-0 lg:border-r">
        <p className="text-sm uppercase tracking-[0.3em] text-orange-400">Assistant IA</p>
        <h2 className="mt-3 text-4xl font-black leading-tight">Un vendeur IA qui qualifie le client.</h2>
        <p className="mt-4 leading-7 text-white/58">Version prototype : l’interface montre le parcours vocal. La vraie voix sera branchée ensuite avec OpenAI Realtime.</p>
        <button onClick={() => setOpen(true)} className="mt-7 rounded-2xl bg-orange-500 px-6 py-4 font-black text-black transition hover:bg-orange-400">🎙️ Démarrer l’assistant</button>
      </div>

      <div className="bg-black/35 p-7">
        <div className="rounded-3xl border border-white/10 bg-[#070707] p-5">
          <div className="mb-5 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-full bg-orange-500 text-xl text-black">AI</div>
              <div>
                <div className="font-black">Agent moteur</div>
                <div className="text-xs text-white/40">Qualification vocale</div>
              </div>
            </div>
            <div className="rounded-full border border-white/10 px-3 py-1 text-xs text-white/50">MVP</div>
          </div>

          <div className="space-y-3">
            <div className="max-w-[85%] rounded-2xl bg-white/10 p-4 text-sm leading-6 text-white/70">Bonjour, je vais vous aider à trouver le bon moteur. Je vais vous poser quelques questions rapides.</div>
            {open && <div className="ml-auto max-w-[85%] rounded-2xl bg-orange-500 p-4 text-sm font-bold leading-6 text-black">{questions[step]}</div>}
          </div>

          {open ? (
            <div className="mt-6 flex flex-wrap gap-3">
              <button onClick={() => setStep((s) => Math.min(s + 1, questions.length - 1))} className="rounded-xl bg-white px-4 py-3 text-sm font-black text-black">Question suivante</button>
              <button onClick={() => { setOpen(false); setStep(0); }} className="rounded-xl border border-white/10 px-4 py-3 text-sm font-bold text-white/65">Réinitialiser</button>
            </div>
          ) : (
            <div className="mt-6 rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm text-white/45">Cliquez sur Démarrer pour voir la simulation.</div>
          )}
        </div>
      </div>
    </div>
  );
}
