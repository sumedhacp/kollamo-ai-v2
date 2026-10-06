/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          800: '#3730a3',
          900: '#312e81',
          950: '#1e1b4b',
        },
        sentiment: {
          positive: {
            DEFAULT: '#10b981',
            light: '#ecfdf5',
            dark: '#047857',
            border: '#a7f3d0'
          },
          negative: {
            DEFAULT: '#ef4444',
            light: '#fef2f2',
            dark: '#b91c1c',
            border: '#fecaca'
          },
          neutral: {
            DEFAULT: '#64748b',
            light: '#f8fafc',
            dark: '#334155',
            border: '#e2e8f0'
          },
          mixed: {
            DEFAULT: '#f59e0b',
            light: '#fffbeb',
            dark: '#b45309',
            border: '#fde68a'
          },
          unsupported: {
            DEFAULT: '#71717a',
            light: '#fafafa',
            dark: '#3f3f46',
            border: '#e4e4e7'
          }
        }
      },
      fontFamily: {
        sans: [
          'Inter',
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'Roboto',
          'Oxygen',
          'Ubuntu',
          'Cantarell',
          'sans-serif',
        ],
      },
    },
  },
  plugins: [],
}
