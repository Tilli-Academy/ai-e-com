/*
 * Auth API calls — thin wrappers over the Django endpoints (confirmed shapes):
 *
 *   POST /auth/register/      {email, first_name, last_name, password, password2}
 *                             -> 201 {id, email, first_name, last_name}   (NO tokens)
 *   POST /auth/login/         {email, password}
 *                             -> 200 {access, refresh, user}
 *   POST /auth/token/refresh/ {refresh} -> 200 {access, refresh}  (rotation on)
 *   POST /auth/logout/        {refresh} + Bearer -> 205
 */
import api from './axios'

export async function registerUser(payload) {
  const { data } = await api.post('/auth/register/', payload)
  return data
}

export async function loginUser({ email, password }) {
  const { data } = await api.post('/auth/login/', { email, password })
  return data   // { access, refresh, user }
}

export async function refreshAccess(refresh) {
  const { data } = await api.post('/auth/token/refresh/', { refresh })
  return data   // { access, refresh }
}

export async function logoutUser(refresh) {
  // Requires the access token (added by the request interceptor) and the
  // refresh token to blacklist.
  const { data } = await api.post('/auth/logout/', { refresh })
  return data
}
