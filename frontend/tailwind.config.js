/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        sentry: {
          bg: "#09090B",
          card: "#18181B",
          cardBorder: "#27272A",
          threatRed: "#FA7273",
          warningAmber: "#F59E0B",
          secureGreen: "#10B981",
          accentIndigo: "#6366F1",
          cyan: "#38BDF8",
          purple: "#A855F7"
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace']
      }
    },
  },
  plugins: [],
}
