import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// ---------------------------------------------------------------------------
// This app is opened through the IDE's reverse proxy at a SUB-PATH:
//   https://<host>:8160/proxy/3002/
// so Vite must generate every URL (JS modules, the Vite/React-Refresh client,
// HMR websocket, and API calls) with that `/proxy/3002/` prefix — otherwise the
// browser requests them at the origin root and the IDE returns 404.
//
// Everything derives from these two numbers, so there's a single place to edit
// if the port or the IDE proxy port ever change.
// ---------------------------------------------------------------------------
const APP_PORT = 3002          // the Vite dev-server port the IDE proxies
const IDE_PROXY_PORT = 8160    // the IDE's public HTTPS port (for the HMR socket)
// code-server has TWO proxy routes:
//   /proxy/<port>/    -> STRIPS the prefix (incompatible with Vite's base: Vite
//                        serves under the prefix, but code-server removes it,
//                        so assets 404 AND root redirects get the prefix added
//                        twice -> /proxy/3002/proxy/3002/).
//   /absproxy/<port>/ -> PRESERVES the full path. Vite receives the prefixed
//                        path it expects, so everything lines up. Use this one.
// Open the app at https://<host>:8160/absproxy/3002/
const BASE = `/absproxy/${APP_PORT}/`

export default defineConfig({
  // `base` makes index.html reference /proxy/3002/src/main.jsx, /@vite/client,
  // /@react-refresh, etc. (all under the proxy path).
  base: BASE,
  plugins: [react()],
  server: {
    host: true,                // listen on all interfaces (reachable via proxy)
    port: APP_PORT,
    strictPort: true,          // fail rather than drift to another port (base is pinned to 3002)
    allowedHosts: true,        // don't block the forwarded Host header (dev only)
    proxy: {
      // Browser calls /proxy/3002/api/... -> strip the proxy prefix -> Django.
      [`${BASE}api`]: {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
        rewrite: (p) => p.replace(BASE.replace(/\/$/, ''), ''),
      },
      [`${BASE}media`]: {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
        rewrite: (p) => p.replace(BASE.replace(/\/$/, ''), ''),
      },
    },
    // HMR websocket must reach the browser through the IDE's HTTPS proxy.
    // If the socket can't connect, live-reload is lost but the PAGE STILL RENDERS.
    hmr: {
      clientPort: IDE_PROXY_PORT,
      path: BASE,
    },
  },
})
