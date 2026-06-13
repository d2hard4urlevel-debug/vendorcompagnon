import AIAssistant from '../components/AIAssistant';
import LeadForm from '../components/LeadForm';

const categories = ['GM 5.3L', 'Ford EcoBoost', 'Ford Coyote', 'Dodge Hemi', 'Honda / Toyota', 'Kia / Hyundai', 'Transmissions'];
const trust = ['Moteurs testés', 'Garantie disponible', 'Livraison Canada', 'Financement possible', 'Installation partenaire'];

export default function Home() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_right,#2b1607,transparent_35%),linear-gradient(180deg,#05070a,#0b0f14_45%,#05070a)] text-white">
      <header className="mx-auto flex max-w-7xl items-center justify-between px-6 py-6">
        <div className="text-xl font-black tracking-tight">MoteurDirect <span className="text-orange-400">AI</span></div>
        <nav className="hidden gap-6 text-sm text-white/70 md:flex">
          <a href="#assistant" className="hover:text-white">Assistant IA</a>
          <a href="#formulaire" className="hover:text-white">Soumission</a>
          <a href="#garanties" className="hover:text-white">Garanties</a>
        </nav>
        <a href="#formulaire" className="rounded-full bg-orange-500 px-5 py-2 font-bold text-black">Trouver mon moteur</a>
      </header>

      <section className="mx-auto grid max-w-7xl items-center gap-10 px-6 py-16 lg:grid-cols-[1.1fr_0.9fr]">
        <div>
          <p className="mb-4 inline-flex rounded-full border border-orange-400/30 bg-orange-500/10 px-4 py-2 text-sm text-orange-200">Assistant IA + moteurs usagés + livraison Canada</p>
          <h1 className="text-5xl font-black leading-tight md:text-7xl">Votre moteur usagé, trouvé plus vite.</h1>
          <p className="mt-6 max-w-2xl text-lg text-white/70">Parlez à notre IA ou envoyez votre demande. On compare les disponibilités, le kilométrage, la garantie et la livraison pour préparer une soumission claire.</p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <a href="#assistant" className="rounded-xl bg-orange-500 px-7 py-4 text-center font-black text-black shadow-glow">🎙️ Parler à l’assistant IA</a>
            <a href="#formulaire" className="rounded-xl border border-white/15 px-7 py-4 text-center font-bold text-white">Recevoir une soumission</a>
          </div>
          <div className="mt-10 grid grid-cols-2 gap-3 md:grid-cols-5">
            {trust.map((item) => <div key={item} className="rounded-2xl border border-white/10 bg-white/[0.04] p-3 text-center text-sm text-white/75">{item}</div>)}
          </div>
        </div>
        <div className="rounded-[2rem] border border-white/10 bg-white/[0.04] p-6 shadow-2xl">
          <div className="rounded-[1.5rem] bg-gradient-to-br from-orange-500/20 to-white/5 p-6">
            <p className="text-sm uppercase tracking-[0.25em] text-orange-300">Soumission instantanée</p>
            <h2 className="mt-3 text-3xl font-black">L’IA pose les questions que les clients oublient.</h2>
            <ul className="mt-6 space-y-3 text-white/75">
              <li>✓ VIN ou 8e digit</li>
              <li>✓ Année, modèle, moteur</li>
              <li>✓ Ville de livraison</li>
              <li>✓ Installation ou livraison seulement</li>
              <li>✓ Budget et urgence</li>
            </ul>
          </div>
        </div>
      </section>

      <section id="assistant" className="mx-auto max-w-7xl px-6 py-12">
        <AIAssistant />
      </section>

      <section className="mx-auto max-w-7xl px-6 py-12">
        <div className="grid gap-4 md:grid-cols-4">
          {['1. Demande', '2. IA confirme', '3. Recherche moteur', '4. Soumission'].map((step) => <div key={step} className="rounded-3xl border border-white/10 bg-white/[0.04] p-6"><h3 className="text-xl font-bold text-orange-300">{step}</h3><p className="mt-2 text-sm text-white/60">Processus simple, rapide et orienté qualité/prix.</p></div>)}
        </div>
      </section>

      <section id="formulaire" className="mx-auto grid max-w-7xl gap-8 px-6 py-12 lg:grid-cols-[0.8fr_1.2fr]">
        <div>
          <p className="text-sm uppercase tracking-[0.25em] text-orange-300">Catalogue populaire</p>
          <h2 className="mt-3 text-4xl font-black">Moteurs et transmissions recherchés.</h2>
          <div className="mt-6 flex flex-wrap gap-3">
            {categories.map((cat) => <span key={cat} className="rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-white/75">{cat}</span>)}
          </div>
          <div id="garanties" className="mt-8 rounded-3xl border border-white/10 bg-white/[0.04] p-6">
            <h3 className="text-2xl font-bold">Confiance avant le prix le plus bas.</h3>
            <p className="mt-3 text-white/65">Le but n’est pas seulement de trouver un moteur. Le but est de trouver l’option qui fait du sens selon le prix, le kilométrage, la garantie et la provenance.</p>
          </div>
        </div>
        <LeadForm />
      </section>

      <footer className="mx-auto max-w-7xl px-6 py-10 text-sm text-white/50">© MoteurDirect AI — Prototype connecté plus tard à VendorCompagnon et Pipedrive.</footer>
    </main>
  );
}
