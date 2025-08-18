/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./**/templates/**/*.html",
    "./static/js/**/*.js",
    "./**/static/js/**/*.js"
  ],
  theme: {
    extend: {
      colors: {
        primary: "#1e3a8a",
        secondary: "#172c6d",
        accent: "#2dd4bf",
        accentHover: "#14b8a6",
        dark: "#111827",
        light: "#f9fafb"
      },
      fontFamily: { sans: ["Poppins", "sans-serif"] },
      boxShadow: {
        card: "0 6px 20px rgba(0,0,0,.06)"
      }
    }
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/typography"),
    require("@tailwindcss/aspect-ratio"),
    require("@tailwindcss/line-clamp")
  ]
}
