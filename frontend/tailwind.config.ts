import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        nero: {
          DEFAULT: '#171717',
          800: '#202020',
          700: '#2A2A2A',
        },
        concrete: '#594542',
        orange: {
          DEFAULT: '#FD5323',
          text: '#B83A12',
        },
        san: '#EEE2D8',
        paper: '#F8F2ED',
        ink: '#360A00',
        muted: {
          light: '#6B5A55',
          dark: '#A8958E',
        },
        line: {
          light: '#E2D3C7',
        },
        status: {
          danger: '#B42318',
          'danger-bg': '#F9E1DC',
          warning: '#8A5A00',
          'warning-bg': '#F6E7C8',
          success: '#2E7D32',
          'success-bg': '#DDEBDD',
          ai: '#7D5A9B',
          'ai-bg': '#E9E0F0',
        },
      },
      fontFamily: {
        sans: ['"Chakra Petch"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      borderRadius: {
        input: '10px',
        card: '16px',
        panel: '24px',
      },
      boxShadow: {
        card: '0 1px 2px rgba(54,10,0,.06), 0 4px 16px rgba(54,10,0,.06)',
      },
    },
  },
  plugins: [],
} satisfies Config
