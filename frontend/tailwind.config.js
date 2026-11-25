/** @type {import('tailwindcss').Config} */

// Colour tokens are driven by CSS variables so the dark theme can swap them
// at runtime. Values are "R G B" triplets consumed as rgb(var(--token) / <a>).
const token = (name) => `rgb(var(${name}) / <alpha-value>)`;

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: token('--color-brand'),
          hover: token('--color-brand-hover'),
          light: token('--color-brand-light'),
        },
        accent: {
          DEFAULT: token('--color-accent'),
          light: token('--color-accent-light'),
        },
        surface: {
          DEFAULT: token('--color-surface'),
          elevated: token('--color-surface-elevated'),
          sunken: token('--color-surface-sunken'),
        },
        text: {
          DEFAULT: token('--color-text'),
          muted: token('--color-text-muted'),
        },
        border: {
          DEFAULT: token('--color-border'),
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
        display: ['Plus Jakarta Sans', 'Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'display-xl': ['4.5rem', { lineHeight: '1.02', letterSpacing: '-0.03em' }],
        'display-lg': ['3.25rem', { lineHeight: '1.05', letterSpacing: '-0.03em' }],
        'display-md': ['2.5rem', { lineHeight: '1.1', letterSpacing: '-0.02em' }],
        'display-sm': ['1.875rem', { lineHeight: '1.15', letterSpacing: '-0.02em' }],
        'heading-lg': ['1.5rem', { lineHeight: '1.3', letterSpacing: '-0.01em' }],
        'heading-md': ['1.25rem', { lineHeight: '1.35', letterSpacing: '-0.01em' }],
        'heading-sm': ['1.0625rem', { lineHeight: '1.4', letterSpacing: '0' }],
        'body-lg': ['1.0625rem', { lineHeight: '1.65' }],
        'body-md': ['0.9375rem', { lineHeight: '1.65' }],
        'body-sm': ['0.8125rem', { lineHeight: '1.55' }],
        caption: ['0.75rem', { lineHeight: '1.5' }],
      },
      spacing: {
        0: '0',
        1: '0.25rem',
        2: '0.5rem',
        3: '0.75rem',
        4: '1rem',
        5: '1.25rem',
        6: '1.5rem',
        8: '2rem',
        10: '2.5rem',
        12: '3rem',
        16: '4rem',
        20: '5rem',
        24: '6rem',
      },
      borderRadius: {
        none: '0',
        sm: '0.25rem',
        DEFAULT: '0.5rem',
        md: '0.75rem',
        lg: '1rem',
        xl: '1.25rem',
        '2xl': '1.75rem',
        '3xl': '2.25rem',
        full: '9999px',
      },
      boxShadow: {
        sm: '0 1px 2px 0 rgb(28 38 32 / 0.05)',
        DEFAULT: '0 1px 3px 0 rgb(28 38 32 / 0.08), 0 1px 2px -1px rgb(28 38 32 / 0.08)',
        md: '0 4px 12px -4px rgb(28 38 32 / 0.12)',
        lg: '0 12px 30px -18px rgb(28 38 32 / 0.35)',
        xl: '0 24px 60px -32px rgb(28 38 32 / 0.45)',
        paper: '0 1px 2px rgb(28 38 32 / 0.04), 0 10px 30px -24px rgb(28 38 32 / 0.4)',
        lift: '0 2px 4px rgb(28 38 32 / 0.05), 0 18px 40px -28px rgb(28 38 32 / 0.55)',
        inner: 'inset 0 2px 4px 0 rgb(28 38 32 / 0.05)',
      },
      transitionDuration: {
        fast: '150ms',
        normal: '200ms',
        slow: '300ms',
      },
      transitionTimingFunction: {
        'ease-out': 'cubic-bezier(0, 0, 0.2, 1)',
        'ease-in-out': 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
      keyframes: {
        rise: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        rise: 'rise 0.45s cubic-bezier(0.22, 1, 0.36, 1) both',
      },
    },
  },
  plugins: [],
};
