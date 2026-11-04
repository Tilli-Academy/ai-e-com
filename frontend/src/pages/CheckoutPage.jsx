/*
 * CheckoutPage — review the cart, enter a shipping address, and place the order
 * via POST /api/orders/. The backend validates stock and computes the final
 * total; on success we go to the confirmation page and refresh the (now-empty)
 * cart. No payment gateway at this stage.
 */
import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useCart } from '../context/CartContext'
import { placeOrder } from '../api/orders'
import { fetchProfile } from '../api/profile'
import { parseApiError } from '../api/errors'
import Loader from '../components/Loader'
import ErrorMessage from '../components/ErrorMessage'

export default function CheckoutPage() {
  const { cart, refreshCart } = useCart()
  const navigate = useNavigate()

  const [loading, setLoading] = useState(true)
  const [address, setAddress] = useState('')
  const [addressError, setAddressError] = useState(null)
  const [formError, setFormError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    let active = true
    ;(async () => {
      setLoading(true)
      await refreshCart()
      try {
        const profile = await fetchProfile()   // prefill from saved address
        if (active && profile?.address) setAddress(profile.address)
      } catch {
        // No profile address — user can type one.
      } finally {
        if (active) setLoading(false)
      }
    })()
    return () => { active = false }
  }, [refreshCart])

  async function handleSubmit(e) {
    e.preventDefault()
    setSubmitting(true)
    setAddressError(null)
    setFormError(null)
    try {
      const order = await placeOrder(address.trim())
      await refreshCart()                       // cart cleared server-side -> reset badge
      navigate(`/order-confirmation/${order.order_number}`, { replace: true })
    } catch (err) {
      const { fieldErrors, nonFieldError } = parseApiError(err)
      if (fieldErrors.shipping_address) setAddressError(fieldErrors.shipping_address)
      setFormError(nonFieldError)               // e.g. empty cart / insufficient stock
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <div className="container page"><Loader /></div>

  const items = cart?.items || []
  if (items.length === 0) {
    return (
      <div className="container page empty-state">
        <h1 className="section-title">Nothing to check out</h1>
        <p>Your cart is empty.</p>
        <p style={{ marginTop: 'var(--space-4)' }}>
          <Link to="/products" className="btn btn-primary">Continue shopping</Link>
        </p>
      </div>
    )
  }

  return (
    <div className="container page">
      <h1 className="section-title">Checkout</h1>

      <div className="cart-layout">
        {/* Shipping form */}
        <form className="card checkout-form" onSubmit={handleSubmit}>
          <h2>Shipping address</h2>
          {formError && <ErrorMessage message={formError} />}
          <div className="form-group">
            <label className="form-label" htmlFor="address">Where should we ship your order?</label>
            <textarea
              id="address" name="address" rows={4}
              className={`form-input ${addressError ? 'has-error' : ''}`}
              value={address} onChange={(e) => setAddress(e.target.value)}
              placeholder="Street, city, postal code…"
            />
            {addressError && <div className="field-error">{addressError}</div>}
            <p className="auth-sub" style={{ marginTop: 'var(--space-2)' }}>
              Leave blank to use the address saved on your profile.
            </p>
          </div>
          <button className="btn btn-primary btn-block" type="submit" disabled={submitting}>
            {submitting ? 'Placing order…' : 'Place order'}
          </button>
        </form>

        {/* Order summary (totals from backend) */}
        <aside className="cart-summary card">
          <h2>Order summary</h2>
          {items.map((item) => (
            <div className="summary-line" key={item.id}>
              <span>{item.product.name} × {item.quantity}</span>
              <span>${item.subtotal}</span>
            </div>
          ))}
          <div className="summary-line summary-total">
            <span>Total</span><span>${cart.total_price}</span>
          </div>
        </aside>
      </div>
    </div>
  )
}
