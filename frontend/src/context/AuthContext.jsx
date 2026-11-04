/*
 * AuthContext — holds the logged-in user and exposes login/logout helpers.
 * Tokens + the cached user live in localStorage (keys from axios.js) so a page
 * refresh keeps the user signed in.
 */
import { createContext, useContext, useEffect, useState } from 'react'
import {
  ACCESS_TOKEN_KEY,
  REFRESH_TOKEN_KEY,
  USER_KEY,
} from '../api/axios'
import { logoutUser } from '../api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? JSON.parse(raw) : null
  })

  useEffect(() => {
    if (user) localStorage.setItem(USER_KEY, JSON.stringify(user))
    else localStorage.removeItem(USER_KEY)
  }, [user])

  // Save tokens + user after a successful login (called by Login/Register pages).
  function login({ access, refresh, user: userData }) {
    if (access) localStorage.setItem(ACCESS_TOKEN_KEY, access)
    if (refresh) localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
    setUser(userData)
  }

  // Blacklist the refresh token on the server (best-effort), then clear locally.
  async function logout() {
    const refresh = localStorage.getItem(REFRESH_TOKEN_KEY)
    if (refresh) {
      try {
        await logoutUser(refresh)
      } catch {
        // Ignore network/blacklist errors — we still clear the client session.
      }
    }
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    setUser(null)
  }

  const value = { user, isAuthenticated: !!user, login, logout, setUser }
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
