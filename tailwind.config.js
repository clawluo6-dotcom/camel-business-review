/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './*.html',
    './scholar-theme.css',
    './cusdis-theme.css',
    './theme-toggle.js',
    './site-data.js',
    './article-content.js',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        bg: { primary:'#0a0e17', secondary:'#111827', card:'#1a1f2e', hover:'#242b3d' },
        accent: {
          cyan:'#22d3ee', purple:'#a855f7', emerald:'#34d399',
          amber:'#fbbf24', rose:'#fb7185', orange:'#fb923c', gold:'#f59e0b'
        },
        text: { primary:'#e2e8f0', secondary:'#94a3b8', muted:'#64748b' }
      }
    }
  },
  plugins: [],
}
