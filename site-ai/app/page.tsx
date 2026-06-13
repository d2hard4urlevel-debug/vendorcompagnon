import AIAssistant from '../components/AIAssistant';
import LeadForm from '../components/LeadForm';

const proof = [
  { value: '90 jours', label: 'garantie disponible' },
  { value: 'Canada', label: 'livraison possible' },
  { value: 'IA', label: 'qualification rapide' },
  { value: 'VIN', label: 'compatibilité validée' },
];

const categories = ['GM 5.3L / 6.2L', 'Ford EcoBoost', 'Ford Coyote', 'Dodge Hemi', 'Honda / Toyota', 'Kia / Hyundai', 'Transmissions'];

const steps = [
  ['01', 'Vous donnez le véhicule', 'Année, modèle, moteur, VIN ou 8e caractère.'],
  ['02', 'L’IA complète les infos', 'Elle pose les questions manquantes avant la recherche.'],
  ['03', 'On compare le marché', 'Prix, kilométrage, garantie, distance et disponibilité.'],
  ['04', 'Soumission claire', 'Vous recevez une option logique, pas juste la moins chère.'],
];

export default function Home() {
  return (
    <main className="min-h-screen bg-[#070707] text-white">
      <section className="relative overflow-hidden border-b border-white/10">
        <div className="absolute inset-0 bg-[linear-gradient(110deg,#070707_0%,#101010_48%,#1b0d03_100%)]" />
        <div className="absolute left-1/2 top-0 h-[520px] w-[520px] -translate-x-1/2 rounded-full bg-orange-500/10 blur-3xl" />
        <div className="relative mx-auto max-w-7xl px-5 py-6">
          <header className="flex items-center justify-between rounded-2xl border border-white/10 bg-black/35 px-5 py-4 backdrop-blur">
            <div>
              <div className="text-lg font-black tracking-tight">MoteurDirect<span className="text-orange-500">AI</span></div>
              <div className="text-xs text-white/45">Moteurs usagés • Soumission rapide</div>
            </div>
            <nav className="hidden items-center gap-7 text-sm text-white/60 md:flex">
              <a href="#assistant" className="hover:text-white">Assistant</a>
              <a href="#process" className="hover:text-white">Processus</a>
              <a href="#formulaire" className="hover:text-white">Soumission</a>
            </nav>
            <a href="#formulaire" className="rounded-xl bg-orange-500 px-5 py-3 text-sm font-black text-black transition hover:bg-orange-400">Demander un prix</a>
          </header>

          <div className="grid items-center gap-12 py-16 lg:grid-cols-[1.05fr_0.95fr] lg:py-24">
            <div>
              <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-orange-500/25 bg-orange-500/10 px-4 py-2 text-sm text-orange-200">
                <span className="h-2 w-2 rounded-full bg-orange-500" /> Assistant IA pour demandes de moteurs
              </div>
              <h1 className="max-w-4xl text-5xl font-black leading-[0.95] tracking-tight md:text-7xl">
                Trouvez le bon moteur sans perdre votre journée.
              </h1>
              <p className="mt-6 max-w-2xl text-lg leading-8 text-white/65">
                Notre assistant prend les informations du véhicule, confirme la compatibilité et prépare une demande claire pour trouver une option fiable selon le prix, le kilométrage et la livraison.
              </p>
              <div className="mt-9 flex flex-col gap-3 sm:flex-row">
                <a href="#assistant" className="rounded-2xl bg-white px-7 py-4 text-center font-black text-black transition hover:bg-orange-100">🎙️ Parler à l’IA</a>
                <a href="#formulaire" className="rounded-2xl border border-white/15 bg-white/5 px-7 py-4 text-center font-bold text-white transition hover:bg-white/10">Remplir le formulaire</a>
              </div>

              <div className="mt-10 grid grid-cols-2 gap-3 md:grid-cols-4">
                {proof.map((item) => (
                  <div key={item.label} className="rounded-2xl border border-white/10 bg-white/[0.035] p-4">
                    <div className="text-2xl font-black text-orange-400">{item.value}</div>
                    <div className="mt-1 text-xs uppercase tracking-wider text-white/45">{item.label}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="relative">
              <div className="absolute -inset-6 rounded-[2.5rem] bg-orange-500/10 blur-2xl" />
              <div className="relative rounded-[2rem] border border-white/10 bg-[#111]/95 p-6 shadow-2xl">
                <div className="rounded-[1.5rem] border border-white/10 bg-black p-5">
                  <div className="mb-5 flex items-center justify-between">
                    <div>
                      <p className="text-xs uppercase tracking-[0.25em] text-orange-400">Analyse moteur</p>
                      <h2 className="mt-2 text-2xl font-black">Demande client</h2>
                    </div>
                    <div className="rounded-full border border-green-400/30 bg-green-400/10 px-3 py-1 text-xs text-green-300">En ligne</div>
                  </div>
                  <div className="space-y-3 text-sm">
                    {['2017 Ford F-150', 'Moteur 5.0L Coyote', 'VIN à confirmer', 'Livraison : Montréal', 'Installation : à discuter'].map((item) => (
                      <div key={item} className="flex items-center justify-between rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3">
                        <span className="text-white/55">{item.split(':')[0]}</span>
                        <span className="font-semibold">{item.includes(':') ? item.split(':').slice(1).join(':').trim() : item}</span>
                      </div>
                    ))}
                  </div>
                  <div className="mt-5 rounded-xl bg-orange-500 p-4 text-black">
                    <p className="text-xs font-bold uppercase tracking-widest">Prochaine action</p>
                    <p className="mt-1 text-lg font-black">Valider le VIN et préparer la soumission</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="assistant" className="mx-auto max-w-7xl px-5 py-16">
        <AIAssistant />
      </section>

      <section id="process" className="mx-auto max-w-7xl px-5 py-10">
        <div className="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-orange-400">Méthode</p>
            <h2 className="mt-3 text-4xl font-black">Simple pour le client, précis pour le vendeur.</h2>
          </div>
          <p className="max-w-xl text-white/55">Le site ne promet pas un prix magique. Il collecte les bonnes informations et prépare une demande vendable.</p>
        </div>
        <div className="grid gap-4 md:grid-cols-4">
          {steps.map(([number, title, text]) => (
            <div key={number} className="rounded-3xl border border-white/10 bg-[#101010] p-6">
              <div className="text-sm font-black text-orange-400">{number}</div>
              <h3 className="mt-5 text-xl font-black">{title}</h3>
              <p className="mt-3 text-sm leading-6 text-white/55">{text}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="formulaire" className="mx-auto grid max-w-7xl gap-8 px-5 py-16 lg:grid-cols-[0.85fr_1.15fr]">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-orange-400">Soumission</p>
          <h2 className="mt-3 text-4xl font-black leading-tight">Demande de moteur usagé.</h2>
          <p className="mt-4 text-white/60">Plus les informations sont précises, plus la recherche est rapide : VIN, moteur exact, ville et installation.</p>
          <div className="mt-7 flex flex-wrap gap-3">
            {categories.map((cat) => (
              <span key={cat} className="rounded-full border border-white/10 bg-white/[0.035] px-4 py-2 text-sm text-white/70">{cat}</span>
            ))}
          </div>
          <div className="mt-8 rounded-3xl border border-white/10 bg-[#101010] p-6">
            <h3 className="text-2xl font-black">Notre positionnement</h3>
            <p className="mt-3 leading-7 text-white/58">On ne cherche pas seulement le moteur le moins cher. On cherche l’option qui a du sens : disponibilité, kilométrage, garantie, fournisseur et logistique.</p>
          </div>
        </div>
        <LeadForm />
      </section>

      <footer className="border-t border-white/10 px-5 py-8 text-center text-sm text-white/40">
        MoteurDirect AI — prototype public relié plus tard à VendorCompagnon.
      </footer>
    </main>
  );
}
