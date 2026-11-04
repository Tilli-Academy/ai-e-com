/*
 * OrderConfirmationPage — shown after a successful checkout. Fetches the order
 * by its number and displays the confirmation (number, status, total, items,
 * shipping address). All values come from the backend.
 */
import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchOrder } from '../api/orders'
import Loader from '../components/Loader'
import ErrorMessage from '../components/ErrorMessage'

export default function OrderConfirmationPage() {
  const { orderNumber } = useParams()
  const [order, setOrder] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setOrder(await fetchOrder(orderNumber))
    } catch {
      setError('Could not load your order confirmation.')
    } finally {
      setLoading(false)
    }
  }, [orderNumber])

  useEffect(() => { load() }, [load])

  if (loading) return <div className="container page"><Loader /></div>
  if (error) return <div className="container page"><ErrorMessage message={error} onRetry={load} /></div>
  if (!order) return null

  return (
    <div className="container page">
      <div className="confirm-banner card">
        <div className="confirm-check">✓</div>
        <h1>Thank you! Your order is placed.</h1>
        <p>Order <strong>{order.order_number}</strong> — status: <span className="badge">{order.status}</span></p>
      </div>

      <div className="cart-layout">
        <aside className="card" style={{ padding: 'var(--space-5)' }}>
          <h2>Items</h2>
          {order.items.map((it) => (
            <div className="summary-line" key={it.id}>
              <span>{it.product_name} × {it.quantity}</span>
              <span>${it.subtotal}</span>
            </div>
          ))}
          <div className="summary-line summary-total">
            <span>Total</span><span>${order.total_price}</span>
          </div>
        </aside>

        <aside className="card" style={{ padding: 'var(--space-5)' }}>
          <h2>Shipping to</h2>
          <p className="detail-desc" style={{ whiteSpace: 'pre-wrap' }}>{order.shipping_address}</p>
          <Link to="/products" className="btn btn-primary btn-block">Continue shopping</Link>
          <Link to="/orders" className="btn btn-outline btn-block" style={{ marginTop: 'var(--space-3)' }}>
            View my orders
          </Link>
        </aside>
      </div>
    </div>
  )
}
