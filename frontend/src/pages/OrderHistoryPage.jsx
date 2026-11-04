/*
 * OrderHistoryPage — "My Orders". Lists the logged-in user's orders (the
 * backend scopes GET /orders/ to request.user). Each row links to the detail
 * page. Handles loading, empty, and error states.
 */
import { useCallback, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { fetchOrders } from '../api/orders'
import StatusBadge from '../components/StatusBadge'
import Loader from '../components/Loader'
import ErrorMessage from '../components/ErrorMessage'

const PAGE_SIZE = 12

function formatDate(iso) {
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric',
  })
}

export default function OrderHistoryPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const page = parseInt(searchParams.get('page') || '1', 10)

  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setData(await fetchOrders(page > 1 ? { page } : {}))
    } catch {
      setError('Could not load your orders. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [page])

  useEffect(() => { load() }, [load])

  function goToPage(p) {
    const next = new URLSearchParams(searchParams)
    if (p > 1) next.set('page', p); else next.delete('page')
    setSearchParams(next)
  }

  if (loading) return <div className="container page"><Loader /></div>
  if (error) return <div className="container page"><ErrorMessage message={error} onRetry={load} /></div>

  const orders = data?.results || []
  if (orders.length === 0) {
    return (
      <div className="container page empty-state">
        <h1 className="section-title">No orders yet</h1>
        <p>When you place an order, it’ll show up here.</p>
        <p style={{ marginTop: 'var(--space-4)' }}>
          <Link to="/products" className="btn btn-primary">Continue shopping</Link>
        </p>
      </div>
    )
  }

  const totalPages = Math.max(1, Math.ceil(data.count / PAGE_SIZE))

  return (
    <div className="container page">
      <h1 className="section-title">My orders</h1>

      <div className="order-list">
        {orders.map((o) => (
          <Link to={`/orders/${o.order_number}`} className="order-row card" key={o.id}>
            <div className="order-row-main">
              <span className="order-number">{o.order_number}</span>
              <span className="order-date">{formatDate(o.created_at)}</span>
            </div>
            <span className="order-items">{o.total_items} item{o.total_items !== 1 ? 's' : ''}</span>
            <span className="order-total">${o.total_price}</span>
            <StatusBadge status={o.status} />
          </Link>
        ))}
      </div>

      {totalPages > 1 && (
        <div className="pagination">
          <button className="btn btn-outline" disabled={!data.previous} onClick={() => goToPage(page - 1)}>← Prev</button>
          <span>Page {page} of {totalPages}</span>
          <button className="btn btn-outline" disabled={!data.next} onClick={() => goToPage(page + 1)}>Next →</button>
        </div>
      )}
    </div>
  )
}
