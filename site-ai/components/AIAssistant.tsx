'use client';

import { useState } from 'react';

const questions = [
  'Quelle est l’année, la marque et le modèle du véhicule?',
  'Connaissez-vous le moteur exact ou le litrages?',
  'Avez-vous le VIN ou le 8e caractère du VIN?',
  'Dans quelle ville doit-on livrer?',
  'Voulez-vous seulement le moteur ou aussi l’installation?',
];

export default function AIAssistant() {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(0);

  return (
    <div className="rounded-3xl border border-orange-400/30 bg-orange-500/10 p-6 shadow-glow">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.25em] text-orange-300">Assistant IA vocal</p>
          <h2 className="mt-2 text-3xl font-bold">Parlez à notre IA moteur</h2>
          <p className="mt-3 text-white/70">L’agent pose les bonnes questions, qualifie la demande et prépare la soumission.</p>
        </div>
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-orange-500 text-3xl text-black">🎙️</div>
      </div>

      <button onClick={() => setOpen(true)} className="mt-6 rounded-xl bg-white px-5 py-3 font-bold text-black transition hover:bg-orange-100">Démarrer l’assistant IA</button>

      {open && (
        <div className="mt-6 rounded-2xl border border-white/10 bg-black/40 p-5">
          <div className="mb-4 flex items-center gap-3">
            <span className="relative flex h-3 w-3">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-orange-400 opacity-75"></span>
              <span className="relative inline-flex h-3 w-3 rounded-full bg-orange-500"></span>
            </span>
            <span className="text-sm text-orange-200">Simulation IA vocale</span>
          </div>
          <p className="text-xl font-semibold">{questions[step]}</p>
          <p className="mt-2 text-sm text-white/55">Version MVP: prochaine étape connecter OpenAI Realtime/WebRTC pour vraie voix.</p>
          <div className="mt-4 flex gap-3">
            <button onClick={() => setStep((s) => Math.min(s + 1, questions.length - 1))} className="rounded-lg bg-orange-500 px-4 py-2 font-bold text-black">Question suivante</button>
            <button onClick={() => setOpen(false)} className="rounded-lg border border-white/15 px-4 py-2 text-white/80">Fermer</button>
          </div>
        </div>
      )}
    </div>
  );
}
