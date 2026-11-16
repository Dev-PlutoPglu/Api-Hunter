import type { Config } from "tailwindcss";
const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      borderRadius: {
        'card': 'var(--radius)',
        'card-lg': 'var(--radius-lg)',
        'card-sm': 'var(--radius-sm)',
      },
      colors: {
        primary: "var(--primary)",
        secondary: "var(--secondary)",
        accent: "var(--accent)",
        muted: "var(--text-dim)",
      },
      boxShadow: {
        'card': 'var(--shadow)',
        'card-lg': 'var(--shadow-lg)',
      },
      backdropBlur: {
        'glass': 'var(--blur)',
      }
    },
  },
  plugins: [],
};
export default config;
