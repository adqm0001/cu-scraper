import { defineConfig, loadEnv, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'

/*
  Injects a Content-Security-Policy meta tag into index.html for production
  builds only. Left out of dev because Vite's own hot-reload (HMR) relies on
  inline scripts and an internal websocket that a strict CSP would block. CSP
  limits where scripts can load from and, crucially, where the page is allowed
  to send data (connect-src) — shrinking the blast radius of any future XSS.
*/
function cspPlugin(apiUrl: string): Plugin {
  const policy = [
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "font-src 'self' https://fonts.gstatic.com",
    "img-src 'self' data:",
    `connect-src 'self' ${apiUrl}`.trim(),
    "object-src 'none'",
    "base-uri 'self'",
  ].join('; ')

  return {
    name: 'inject-csp',
    apply: 'build',
    transformIndexHtml(html) {
      return html.replace(
        '</title>',
        `</title>\n    <meta http-equiv="Content-Security-Policy" content="${policy}" />`
      )
    },
  }
}

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [react(), cspPlugin(env.VITE_API_URL ?? '')],
  }
})
