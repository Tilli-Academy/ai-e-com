/*
 * CartContext — holds the cart item-count for the navbar badge and the
 * add-to-cart action. The full cart object/management lands in 6.4; for now we
 * expose `itemCount`, `refreshCart`, and `addItem`.
 *
 * The cart only exists for authenticated users, so we fetch it when the user is
 * logged in and reset to empty on logout.
 */
import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import {
  addToCart,
  clearCart,
  fetchCart,
  removeCartItem,
  updateCartItem,
} from '../api/cart'
import { useAuth } from './AuthContext'

const CartContext = createContext(null)

export function CartProvider({ children }) {
  const { isAuthenticated } = useAuth()
  const [itemCount, setItemCount] = useState(0)
  const [cart, setCart] = useState(null)

  const refreshCart = useCallback(async () => {
    if (!isAuthenticated) {
      setCart(null)
      setItemCount(0)
      return
    }
    try {
      const data = await fetchCart()
      setCart(data)
      setItemCount(data.total_items)
    } catch {
      // Non-fatal: leave the badge as-is if the fetch fails.
    }
  }, [isAuthenticated])

  // Refresh whenever auth state changes (login/logout).
  useEffect(() => { refreshCart() }, [refreshCart])

  // Add a product, then refresh the count. Throws on API error so callers can
  // show a message (e.g. out-of-stock race).
  async function addItem(productId, quantity = 1) {
    await addToCart(productId, quantity)
    await refreshCart()
  }

  // Cart-page actions. Each refreshes afterwards so totals/badge stay in sync.
  // They rethrow API errors so the page can surface stock messages.
  async function updateItem(itemId, quantity) {
    await updateCartItem(itemId, quantity)
    await refreshCart()
  }
  async function removeItem(itemId) {
    await removeCartItem(itemId)
    await refreshCart()
  }
  async function clear() {
    await clearCart()
    await refreshCart()
  }

  const value = {
    itemCount, cart, refreshCart, addItem, updateItem, removeItem, clear,
  }
  return <CartContext.Provider value={value}>{children}</CartContext.Provider>
}

export function useCart() {
  const ctx = useContext(CartContext)
  if (!ctx) throw new Error('useCart must be used inside <CartProvider>')
  return ctx
}
