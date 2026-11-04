/*
 * Cart API calls. All require authentication (handled by the Axios interceptors).
 *
 *   GET    /cart/              -> { id, items:[...], total_items, total_price }
 *   POST   /cart/items/        { product, quantity } -> add/increment
 *   PATCH  /cart/items/{id}/   { quantity }          -> SET quantity
 *   DELETE /cart/items/{id}/                         -> remove one line
 *   DELETE /cart/clear/                              -> empty the cart
 */
import api from './axios'

export async function fetchCart() {
  const { data } = await api.get('/cart/')
  return data
}

export async function addToCart(productId, quantity = 1) {
  const { data } = await api.post('/cart/items/', { product: productId, quantity })
  return data
}

export async function updateCartItem(itemId, quantity) {
  const { data } = await api.patch(`/cart/items/${itemId}/`, { quantity })
  return data
}

export async function removeCartItem(itemId) {
  await api.delete(`/cart/items/${itemId}/`)
}

export async function clearCart() {
  await api.delete('/cart/clear/')
}
