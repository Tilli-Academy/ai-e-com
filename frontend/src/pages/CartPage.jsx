/*
 * CartPage — the logged-in user's shopping cart.
 *
 * Loads the cart from the API (via CartContext), lets the user change quantities
 * and remove items, and shows the backend-computed line subtotals and total.
 * All totals come from the API — the frontend never computes authoritative money.
 */
import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useCart } from '../context/CartContext'
import { resolveMediaUrl } from '../api/media'
import { parseApiError } from '../api/errors'
import { clampQuantity } from '../utils/quantity'
import Loader from '../components/Loader'
import ErrorMessage from '../components/ErrorMessage'

export default function CartPage() {
  const { cart, refreshCart, updateItem, removeItem, clear } = useCart()
  const navigate = useNavigate()

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [busyId, setBusyId] = useState(null)       // item currently updating
  const [itemErrors, setItemErrors] = useState({}) // { [itemId]: message }

  useEffect(() => {
    let active = true
    ;(async () => {
      setLoading(true)
      setError(null)
      try {
        await refreshCart()
      } catch {
        if (active) setError('Could not load your cart. Please try again.')
      } finally {
        if (active) setLoading(false)
      }
    })()
    return () => { active = false }
  }, [refreshCart])

  async function changeQty(item, nextQty) {
    const qty = clampQuantity(nextQty, item.product.stock)
    if (qty === item.quantity) return
    setBusyId(item.id)
    setItemErrors((e) => ({ ...e, [item.id]: null }))
    try {
      await updateItem(item.id, qty)
    } catch (err) {
      const { nonFieldError, fieldErrors } = parseApiError(err)
      setItemErrors((e) => ({
        ...e,
        [item.id]: fieldErrors.quantity || nonFieldError || 'Could not update quantity.',
      }))
    } finally {
      setBusyId(null)
    }
  }

  async function remove(item) {
    setBusyId(item.id)
    try {
      await removeItem(item.id)
    } finally {
      setBusyId(null)
    }
  }

  if (loading) return <div className="container page"><Loader /></div>
  if (error) return <div className="container page"><ErrorMessage message={error} onRetry={refreshCart} /></div>

  const items = cart?.items || []

  if (items.length === 0) {
    return (
      <div className="container page empty-state">
        <h1 className="section-title">Your cart is empty</h1>
        <p>Browse the catalog and add something you like.</p>
        <p style={{ marginTop: 'var(--space-4)' }}>
          <Link to="/products" className="btn btn-primary">Continue shopping</Link>
        </p>
      </div>
    )
  }

  return (
    <div className="container page">
      <h1 className="section-title">Your cart</h1>

      <div className="cart-layout">
        <div className="cart-items">
          {items.map((item) => {
            const { product } = item
            const imgUrl = resolveMediaUrl(product.image)
            const atMax = item.quantity >= product.stock
            const busy = busyId === item.id
            return (
              <div className="cart-row" key={item.id}>
                <Link to={`/products/${product.slug}`} className="cart-thumb">
                  {imgUrl ? <img src={imgUrl} alt={product.name} /> : <span>{product.name.charAt(0)}</span>}
                </Link>
                <div className="cart-info">
                  <Link to={`/products/${product.slug}`} className="cart-name">{product.name}</Link>
                  <span className="cart-unit">${product.price} each</span>
                  {itemErrors[item.id] && <div className="field-error">{itemErrors[item.id]}</div>}
                </div>
                <div className="cart-qty">
                  <button className="qty-btn" disabled={busy || item.quantity <= 1}
                          onClick={() => changeQty(item, item.quantity - 1)} aria-label="Decrease">−</button>
                  <span className="qty-val">{item.quantity}</span>
                  <button className="qty-btn" disabled={busy || atMax}
                          onClick={() => changeQty(item, item.quantity + 1)} aria-label="Increase">+</button>
                </div>
                <div className="cart-subtotal">${item.subtotal}</div>
                <button className="cart-remove" disabled={busy} onClick={() => remove(item)} aria-label="Remove">
                  Remove
                </button>
              </div>
            )
          })}
        </div>

        {/* Summary — totals from the backend */}
        <aside className="cart-summary card">
          <h2>Summary</h2>
          <div className="summary-line">
            <span>Items</span><span>{cart.total_items}</span>
          </div>
          <div className="summary-line summary-total">
            <span>Total</span><span>${cart.total_price}</span>
          </div>
          <button className="btn btn-primary btn-block" onClick={() => navigate('/checkout')}>
            Proceed to Checkout
          </button>
          <Link to="/products" className="btn btn-outline btn-block" style={{ marginTop: 'var(--space-3)' }}>
            Continue shopping
          </Link>
          <button className="btn-link" onClick={clear} style={{ marginTop: 'var(--space-3)' }}>
            Clear cart
          </button>
        </aside>
      </div>
    </div>
  )
}
