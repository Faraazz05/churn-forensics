import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          900: '#0A0D1A',
          800: '#0F1629',
          700: '#141E35',
          600: '#1E2A45'
        }
      }
    },
  },
  plugins: [],
} satisfies Config
