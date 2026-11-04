/*
 * OrderDetailPage — a single order (GET /orders/{order_number}/). The backend
 * scopes it to the user, so another user's order returns 404 (handled below).
 * Shows items with snapshot name/price/qty/subtotal, total, status, shipping.
 */
import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchOrder } from '../api/orders'
import StatusBadge from '../components/StatusBadge'
import Loader from '../components/Loader'
import ErrorMessage from '../components/ErrorMessage'

function formatDate(iso) {
  return new Date(iso).toLocaleString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

export default function OrderDetailPage() {
  const { orderNumber } = useParams()
  const [order, setOrder] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [notFound, setNotFound] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    setNotFound(false)
    try {
      setOrder(await fetchOrder(orderNumber))
    } catch (err) {
      if (err.response?.status === 404) setNotFound(true)
      else setError('Could not load this order. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [orderNumber])

  useEffect(() => { load() }, [load])

  if (loading) return <div className="container page"><Loader /></div>
  if (notFound) return (
    <div className="container page empty-state">
      <h1 className="section-title">Order not found</h1>
      <p>We couldn’t find that order under your account.</p>
      <p style={{ marginTop: 'var(--space-4)' }}><Link to="/orders" className="btn btn-primary">Back to my orders</Link></p>
    </div>
  )
  if (error) return <div className="container page"><ErrorMessage message={error} onRetry={load} /></div>
  if (!order) return null

  return (
    <div className="container page">
      <p style={{ marginBottom: 'var(--space-4)' }}>
        <Link to="/orders" className="navbar-link">← Back to my orders</Link>
      </p>

      <div className="order-detail-head card">
        <div>
          <h1 style={{ fontSize: '1.4rem' }}>Order {order.order_number}</h1>
          <p className="order-date">{formatDate(order.created_at)}</p>
        </div>
        <StatusBadge status={order.status} />
      </div>

      <div className="cart-layout" style={{ marginTop: 'var(--space-5)' }}>
        <aside className="card" style={{ padding: 'var(--space-5)' }}>
          <h2>Items</h2>
          {order.items.map((it) => (
            <div className="summary-line" key={it.id}>
              <span>
                {it.product_slug
                  ? <Link to={`/products/${it.product_slug}`}>{it.product_name}</Link>
                  : it.product_name}
                {' '}× {it.quantity} <span className="cart-unit">(${it.price} each)</span>
              </span>
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
        </aside>
      </div>
    </div>
  )
}
