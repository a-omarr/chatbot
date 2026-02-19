/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        brand: {
          cyan: '#06b6d4',
          sky: '#0ea5e9',
          violet: '#8b5cf6',
        },
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        "fade-in-up": {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "pulse-slow": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.5" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200%" },
          "100%": { backgroundPosition: "200%" },
        },
        "glow-pulse": {
          "0%, 100%": { boxShadow: "0 0 20px -5px rgba(56,189,248,0.3)" },
          "50%": { boxShadow: "0 0 40px -5px rgba(56,189,248,0.5)" },
        },
        "gradient-shift": {
          "0%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
          "100%": { backgroundPosition: "0% 50%" },
        },
        float: {
          "0%, 100%": { transform: "translate(0,0) scale(1)" },
          "25%": { transform: "translate(30px,-30px) scale(1.05)" },
          "50%": { transform: "translate(-20px,20px) scale(0.95)" },
          "75%": { transform: "translate(20px,10px) scale(1.02)" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "fade-in-up": "fade-in-up 0.3s ease-out forwards",
        "pulse-slow": "pulse-slow 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        shimmer: "shimmer 2s linear infinite",
        "glow-pulse": "glow-pulse 3s ease-in-out infinite",
        "gradient-shift": "gradient-shift 6s ease infinite",
        float: "float 20s ease-in-out infinite",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
