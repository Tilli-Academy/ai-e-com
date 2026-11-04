/*
 * Central Axios instance + JWT interceptors.
 *
 * baseURL is `${BASE_URL}api` — under the code-server proxy that resolves to
 * "/absproxy/3002/api", which the Vite dev proxy forwards to Django. Same-origin,
 * no CORS, no hardcoded backend port.
 *
 * Request interceptor : attaches the access token.
 * Response interceptor: on a 401, transparently refreshes the access token once
 *                       (using the refresh token) and retries the request. If
 *                       refresh fails, it clears the session and sends the user
 *                       to the login page.
 */
import axios from 'axios'

// Single source of truth for the localStorage keys (reused by AuthContext).
export const ACCESS_TOKEN_KEY = 'access_token'
export const REFRESH_TOKEN_KEY = 'refresh_token'
export const USER_KEY = 'auth_user'

const api = axios.create({
  baseURL: `${import.meta.env.BASE_URL}api`,
  headers: { 'Content-Type': 'application/json' },
})

// --- Request: attach the access token when present ---------------------------
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(ACCESS_TOKEN_KEY)
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// --- Helpers ----------------------------------------------------------------
function clearSession() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

function redirectToLogin() {
  // Full navigation to the login route (honours the Vite base path). Avoids
  // doing it repeatedly if we're already there.
  const loginPath = `${import.meta.env.BASE_URL}login`
  if (!window.location.pathname.endsWith('/login')) {
    window.location.assign(loginPath)
  }
}

// Endpoints that must NOT trigger the refresh-and-retry flow (they ARE the auth
// flow, so a 401 from them is a real failure to surface to the caller).
function isAuthEndpoint(url = '') {
  return url.includes('/auth/login/') || url.includes('/auth/token/refresh/')
}

// --- Single-flight refresh --------------------------------------------------
// The backend ROTATES refresh tokens, so two concurrent refreshes would make
// the second one fail. We therefore run at most one refresh at a time and queue
// any requests that 401 while it's in flight.
let refreshPromise = null

function refreshAccessToken() {
  if (!refreshPromise) {
    const refresh = localStorage.getItem(REFRESH_TOKEN_KEY)
    if (!refresh) return Promise.reject(new Error('no refresh token'))
    // Bare axios (not `api`) so this call skips the interceptors below.
    refreshPromise = axios
      .post(`${import.meta.env.BASE_URL}api/auth/token/refresh/`, { refresh })
      .then(({ data }) => {
        localStorage.setItem(ACCESS_TOKEN_KEY, data.access)
        if (data.refresh) localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh)
        return data.access
      })
      .finally(() => { refreshPromise = null })
  }
  return refreshPromise
}

// --- Response: refresh-and-retry on 401 -------------------------------------
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    const status = error.response?.status

    if (status === 401 && original && !original._retry && !isAuthEndpoint(original.url)) {
      original._retry = true
      try {
        const newAccess = await refreshAccessToken()
        original.headers.Authorization = `Bearer ${newAccess}`
        return api(original)   // retry the original request once
      } catch (refreshError) {
        clearSession()
        redirectToLogin()
        return Promise.reject(refreshError)
      }
    }
    return Promise.reject(error)
  },
)

export default api
