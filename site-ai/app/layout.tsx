import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'MoteurDirect AI | Moteurs usagés au Canada',
  description: 'Assistant IA pour trouver un moteur usagé testé avec livraison au Canada.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
