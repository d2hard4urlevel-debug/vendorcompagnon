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
  installation: 'À confirmer',
  budget: '',
  message: '',
};

function inputClass() {
  return 'rounded-2xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white outline-none transition placeholder:text-white/28 focus:border-orange-500';
}

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
    <form onSubmit={submit} className="rounded-[2rem] border border-white/10 bg-[#101010] p-6 shadow-2xl">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-orange-400">Formulaire</p>
          <h2 className="mt-3 text-3xl font-black">Recevoir une soumission</h2>
          <p className="mt-2 text-sm leading-6 text-white/50">Entrez ce que vous savez. Le VIN aide à éviter les erreurs de compatibilité.</p>
        </div>
        <div className="hidden rounded-2xl border border-white/10 bg-black/40 px-4 py-3 text-right md:block">
          <div className="text-xs text-white/35">Statut</div>
          <div className="font-black text-orange-400">Prioritaire</div>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <input className={inputClass()} placeholder="Nom complet" value={lead.nom} onChange={(e) => update('nom', e.target.value)} />
        <input className={inputClass()} placeholder="Téléphone" value={lead.telephone} onChange={(e) => update('telephone', e.target.value)} />
        <input className={inputClass()} placeholder="Email" value={lead.email} onChange={(e) => update('email', e.target.value)} />
        <input className={inputClass()} placeholder="Ville de livraison" value={lead.ville} onChange={(e) => update('ville', e.target.value)} />
        <input className={inputClass()} placeholder="Année" value={lead.annee} onChange={(e) => update('annee', e.target.value)} />
        <input className={inputClass()} placeholder="Marque" value={lead.marque} onChange={(e) => update('marque', e.target.value)} />
        <input className={inputClass()} placeholder="Modèle" value={lead.modele} onChange={(e) => update('modele', e.target.value)} />
        <input className={inputClass()} placeholder="Moteur ex: 5.3L, 3.5L, 2.4L" value={lead.moteur} onChange={(e) => update('moteur', e.target.value)} />
        <input className={`${inputClass()} md:col-span-2`} placeholder="VIN complet ou 8e caractère du VIN" value={lead.vin} onChange={(e) => update('vin', e.target.value)} />
        <select className={inputClass()} value={lead.installation} onChange={(e) => update('installation', e.target.value)}>
          <option>À confirmer</option>
          <option>Livraison seulement</option>
          <option>Installation aussi</option>
        </select>
        <input className={inputClass()} placeholder="Budget approximatif" value={lead.budget} onChange={(e) => update('budget', e.target.value)} />
        <textarea className={`${inputClass()} min-h-28 md:col-span-2`} placeholder="Détails, urgence, problème du véhicule..." value={lead.message} onChange={(e) => update('message', e.target.value)} />
      </div>

      <button className="mt-5 w-full rounded-2xl bg-orange-500 px-5 py-4 font-black text-black transition hover:bg-orange-400">Envoyer la demande</button>
      {sent && <p className="mt-4 rounded-2xl border border-green-400/25 bg-green-400/10 p-4 text-sm text-green-200">Demande enregistrée en mode prototype. Prochaine étape : connexion à VendorCompagnon / Pipedrive.</p>}
    </form>
  );
}
