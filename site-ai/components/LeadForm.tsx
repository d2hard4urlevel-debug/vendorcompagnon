'use client';

import { useState } from 'react';

const emptyLead = {
  nom: '',
  telephone: '',
  email: '',
  annee: '',
  marque: '',
  modele: '',
  moteur: '',
  vin: '',
  ville: '',
  installation: 'Non',
  budget: '',
  message: '',
};

export default function LeadForm() {
  const [lead, setLead] = useState(emptyLead);
  const [sent, setSent] = useState(false);

  function update(field: string, value: string) {
    setLead((current) => ({ ...current, [field]: value }));
  }

  function submit(event: React.FormEvent) {
    event.preventDefault();
    setSent(true);
    console.log('Lead moteur', lead);
  }

  return (
    <form onSubmit={submit} className="rounded-3xl border border-white/10 bg-white/[0.04] p-6 shadow-glow">
      <div className="mb-6">
        <p className="text-sm uppercase tracking-[0.25em] text-orange-400">Soumission rapide</p>
        <h2 className="mt-2 text-3xl font-bold">Trouver mon moteur</h2>
        <p className="mt-2 text-sm text-white/60">Entrez les informations connues. L'assistant IA demandera les détails manquants.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <input className="rounded-xl border border-white/10 bg-black/30 p-3 outline-none focus:border-orange-400" placeholder="Nom" value={lead.nom} onChange={(e) => update('nom', e.target.value)} />
        <input className="rounded-xl border border-white/10 bg-black/30 p-3 outline-none focus:border-orange-400" placeholder="Téléphone" value={lead.telephone} onChange={(e) => update('telephone', e.target.value)} />
        <input className="rounded-xl border border-white/10 bg-black/30 p-3 outline-none focus:border-orange-400" placeholder="Email" value={lead.email} onChange={(e) => update('email', e.target.value)} />
        <input className="rounded-xl border border-white/10 bg-black/30 p-3 outline-none focus:border-orange-400" placeholder="Ville de livraison" value={lead.ville} onChange={(e) => update('ville', e.target.value)} />
        <input className="rounded-xl border border-white/10 bg-black/30 p-3 outline-none focus:border-orange-400" placeholder="Année" value={lead.annee} onChange={(e) => update('annee', e.target.value)} />
        <input className="rounded-xl border border-white/10 bg-black/30 p-3 outline-none focus:border-orange-400" placeholder="Marque" value={lead.marque} onChange={(e) => update('marque', e.target.value)} />
        <input className="rounded-xl border border-white/10 bg-black/30 p-3 outline-none focus:border-orange-400" placeholder="Modèle" value={lead.modele} onChange={(e) => update('modele', e.target.value)} />
        <input className="rounded-xl border border-white/10 bg-black/30 p-3 outline-none focus:border-orange-400" placeholder="Moteur / litrages" value={lead.moteur} onChange={(e) => update('moteur', e.target.value)} />
        <input className="rounded-xl border border-white/10 bg-black/30 p-3 outline-none focus:border-orange-400 md:col-span-2" placeholder="VIN ou 8e caractère du VIN" value={lead.vin} onChange={(e) => update('vin', e.target.value)} />
        <select className="rounded-xl border border-white/10 bg-black/30 p-3 outline-none focus:border-orange-400" value={lead.installation} onChange={(e) => update('installation', e.target.value)}>
          <option>Non</option>
          <option>Oui</option>
          <option>À confirmer</option>
        </select>
        <input className="rounded-xl border border-white/10 bg-black/30 p-3 outline-none focus:border-orange-400" placeholder="Budget approximatif" value={lead.budget} onChange={(e) => update('budget', e.target.value)} />
        <textarea className="min-h-28 rounded-xl border border-white/10 bg-black/30 p-3 outline-none focus:border-orange-400 md:col-span-2" placeholder="Message / détails" value={lead.message} onChange={(e) => update('message', e.target.value)} />
      </div>

      <button className="mt-5 w-full rounded-xl bg-orange-500 px-5 py-4 font-bold text-black transition hover:bg-orange-400">Recevoir ma soumission</button>
      {sent && <p className="mt-4 rounded-xl border border-green-400/30 bg-green-400/10 p-3 text-sm text-green-200">Demande prête. Prochaine étape: connecter ce formulaire à VendorCompagnon/Pipedrive.</p>}
    </form>
  );
}
