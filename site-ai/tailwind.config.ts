import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{js,ts,jsx,tsx}', './components/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        mechanic: '#f97316',
        graphite: '#0b0f14',
        steel: '#17202a',
      },
      boxShadow: {
        glow: '0 0 40px rgba(249, 115, 22, 0.25)',
      },
    },
  },
  plugins: [],
};

export default config;
