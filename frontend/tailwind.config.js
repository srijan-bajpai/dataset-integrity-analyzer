/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: 'var(--background)',
        foreground: 'var(--foreground)',
        card: 'var(--card)',
        'card-foreground': 'var(--card-foreground)',
        border: 'var(--border)',
        muted: 'var(--muted)',
        'muted-foreground': 'var(--muted-foreground)',
        well: 'var(--well)',
        warm: {
          alabaster: '#FAF8F5',
          paper: '#FDFBF7',
          sand: '#F3F0EA',
          border: '#E7E5E0',
          charcoal: '#1C1917',
          slate: '#57534E',
        },
        sage: {
          50: '#F0FDF4',
          100: '#DCFCE7',
          200: '#BBF7D0',
          500: '#22C55E',
          600: '#16A34A',
          700: '#15803D',
          800: '#166534',
        },
        ochre: {
          50: '#FFFBEB',
          100: '#FEF3C7',
          200: '#FDE68A',
          500: '#F59E0B',
          600: '#D97706',
          700: '#B45309',
          800: '#92400E',
        },
        terracotta: {
          50: '#FFF1F2',
          100: '#FFE4E6',
          200: '#FECDD3',
          500: '#F43F5E',
          600: '#E11D48',
          700: '#BE123C',
          800: '#9F1239',
        },
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
        '4xl': '2rem',
      },
      boxShadow: {
        'warm-sm': '0 2px 8px -2px rgba(28, 25, 23, 0.04), 0 1px 3px -1px rgba(28, 25, 23, 0.02)',
        'warm-md': '0 8px 24px -4px rgba(28, 25, 23, 0.06), 0 2px 6px -1px rgba(28, 25, 23, 0.03)',
        'warm-lg': '0 16px 36px -6px rgba(28, 25, 23, 0.08), 0 4px 12px -2px rgba(28, 25, 23, 0.04)',
        'glass': '0 8px 32px 0 rgba(28, 25, 23, 0.08)',
        'glass-sm': '0 4px 16px 0 rgba(28, 25, 23, 0.05)',
      },
    },
  },
  plugins: [],
}
