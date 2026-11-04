/*
 * Profile API. Used by checkout to prefill the shipping address.
 *   GET /auth/profile/ -> { id, user, phone, address, ... }
 */
import api from './axios'

export async function fetchProfile() {
  const { data } = await api.get('/auth/profile/')
  return data
}
