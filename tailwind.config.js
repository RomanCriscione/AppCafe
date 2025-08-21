/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./**/*.html",
    "./static/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#2563eb',
          50:  '#eff6ff',
          100: '#dbeafe',
          600: '#1d4ed8',
          700: '#1e40af',
        },
        // Por si quedó algo usando 'secondary', lo igualamos al azul:
        secondary: '#2563eb',
        accent: '#10b981',
      },
      boxShadow: {
        card: "0 10px 25px rgba(2,8,23,.06)",
      },
    },
  },
  plugins: [],
}
