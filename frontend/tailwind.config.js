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
          DEFAULT: '#F8FAFC',
          dark: '#E2E8F0',
          card: '#FFFFFF',
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
        palette: {
          blue1: '#19AADE',
          blue2: '#1AC9E6',
          teal1: '#1DE4BD',
          teal2: '#6DF0D2',
          purple1: '#AF4BCE',
          pink1: '#DB4CB2',
          pink2: '#EB548C',
          pink3: '#EA7369',
          pink4: '#F0A58F',
          orange1: '#DE542C',
          orange2: '#EF7E32',
          orange3: '#EE9A3A',
          yellow1: '#EABD3B',
          yellow2: '#E7E34E'
        },
        text: {
          primary: '#0F172A',
          muted: '#64748B'
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
