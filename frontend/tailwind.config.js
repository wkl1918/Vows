/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        midnighthue: '#1e1b4b',
        primary: '#4f46e5',
        secondary: '#64748b',
      }
    },
  },
  plugins: [],
}

