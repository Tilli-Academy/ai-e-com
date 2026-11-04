/*
 * Assistant API. Reuses the shared Axios instance, so the JWT access token is
 * attached automatically (needed for authenticated order-status queries) and
 * the call goes through the Vite proxy to Django — the browser never contacts
 * Ollama directly.
 *
 *   POST /assistant/chat/  { message }
 *     -> { reply, degraded, intent, products: [...] }
 */
import api from './axios'

export async function sendChatMessage(message) {
  const { data } = await api.post('/assistant/chat/', { message })
  return data
}

// Products for the homepage "Recommended for You" section. Reuses the backend
// rule-based recommender (no LLM); returns full product objects (same shape as
// the catalog) so <ProductCard> renders them directly.
export async function fetchRecommendations() {
  const { data } = await api.get('/assistant/recommendations/')
  return data.products
}
