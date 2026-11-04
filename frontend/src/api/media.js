/*
 * resolveMediaUrl — make a backend image URL loadable by the browser.
 *
 * Django's ImageField returns an ABSOLUTE url built from the request host, e.g.
 * "http://127.0.0.1:8001/media/products/x.png". The browser (on the code-server
 * HTTPS origin) can't load that — it bypasses the proxy and is mixed-content.
 *
 * We keep only the path ("/media/products/x.png") and prefix it with Vite's
 * BASE_URL so the request goes through the proxy:
 *   "/absproxy/3002/media/products/x.png" -> Vite /media proxy -> Django.
 * Works unchanged in a plain setup where BASE_URL is "/".
 *
 * Returns null for a missing image so callers can show their placeholder.
 */
export function resolveMediaUrl(url) {
  if (!url) return null
  let path = url
  try {
    path = new URL(url).pathname          // strips scheme + host
  } catch {
    // already a relative path — use as-is
  }
  const base = import.meta.env.BASE_URL || '/'
  return `${base}${path.replace(/^\/+/, '')}`
}
