/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./**/templates/**/*.html",
    "./static/**/*.js",
    "./reviews/**/*.py",
    "./core/**/*.py"
  ],
  safelist: [
    // alturas y límites usados en templates/JS
    'max-h-[1056px]',
    'h-[250px]', 'sm:h-[350px]', 'md:h-[450px]', 'lg:h-[550px]',
    // z-index enormes para toasts y overlays
    'z-[2147483000]', 'z-[2147485000]',
    // transforms usados por el drawer móvil
    '-translate-x-full', 'translate-x-0',
    // opacidades del overlay
    'opacity-0', 'opacity-100'
  ],
  theme: {
    extend: {
      fontFamily: { sans: ["Poppins","ui-sans-serif","system-ui"] },
      colors: {
        brand: {
          50:"#F7F3F0",100:"#F1E8E3",200:"#E7D7C9",300:"#E6CCB2",
          400:"#DDB892",500:"#B08968",600:"#996B53",
          700:"#7A4F2A",800:"#6B4426",900:"#55351E"
        }
      },
      boxShadow: {
        soft: "0 6px 24px -8px rgba(16,24,40,.08)",
        card: "0 10px 25px rgba(2,8,23,.06)"
      },
      borderRadius: { xl: "1rem", "2xl": "1.25rem" }
    }
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/typography"),
    require("@tailwindcss/aspect-ratio"),
    require("@tailwindcss/line-clamp")
  ]
};
