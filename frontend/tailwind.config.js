/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: '#0E1E25',
          dark: '#12232B',
          card: '#162A33',
        },
        accent: {
          DEFAULT: '#00AD9F',
          teal: '#00AD9F',
          cyan: '#2DD4BF',
        },
        status: {
          r: '#F4503B',
          i: '#F5A623',
          s: '#2BC48A',
          none: '#6B7C85'
        },
        text: {
          primary: '#E6EDF0',
          muted: '#8FA3AD'
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      }
    },
  },
  plugins: [],
}
