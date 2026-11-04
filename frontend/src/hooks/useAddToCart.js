/*
 * useAddToCart — shared add-to-cart logic for cards and the detail page.
 *
 * - If the user isn't logged in, redirect to /login (remembering the current
 *   page) and return { status: 'auth' }.
 * - Otherwise call the cart API and return { status: 'ok' } or
 *   { status: 'error', message } so the caller can show feedback.
 */
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useCart } from '../context/CartContext'
import { parseApiError } from '../api/errors'

export function useAddToCart() {
  const { isAuthenticated } = useAuth()
  const { addItem } = useCart()
  const navigate = useNavigate()
  const location = useLocation()

  return async function add(product, quantity = 1) {
    if (!isAuthenticated) {
      navigate('/login', { state: { from: location } })
      return { status: 'auth' }
    }
    try {
      await addItem(product.id, quantity)
      return { status: 'ok' }
    } catch (err) {
      const { nonFieldError, fieldErrors } = parseApiError(err)
      const message =
        nonFieldError || Object.values(fieldErrors)[0] || 'Could not add to cart.'
      return { status: 'error', message }
    }
  }
}
