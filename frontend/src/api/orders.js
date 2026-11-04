/*
 * Order API calls.
 *
 *   GET  /orders/                 -> paginated list of the user's orders
 *   POST /orders/                 { shipping_address? } -> 201 order
 *   GET  /orders/{order_number}/                        -> order detail
 * All require authentication and are scoped to the current user by the backend.
 */
import api from './axios'

export async function fetchOrders(params = {}) {
  const { data } = await api.get('/orders/', { params })
  return data   // { count, next, previous, results: [...] }
}

export async function placeOrder(shippingAddress) {
  const { data } = await api.post('/orders/', { shipping_address: shippingAddress })
  return data   // full order (order_number, total_price, items, ...)
}

export async function fetchOrder(orderNumber) {
  const { data } = await api.get(`/orders/${orderNumber}/`)
  return data
}
