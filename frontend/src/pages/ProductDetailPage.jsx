/*
 * ProductDetailPage — single product view fetched by slug from
 * GET /api/products/<slug>/. Shows image, name, category, price, stock
 * availability, description, a quantity selector, and an Add-to-Cart button
 * (disabled when unavailable/out of stock). Handles loading, not-found (404),
 * and generic errors.
 */
import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct } from '../api/products'
import { resolveMediaUrl } from '../api/media'
import { useAddToCart } from '../hooks/useAddToCart'
import Loader from '../components/Loader'
import ErrorMessage from '../components/ErrorMessage'

export default function ProductDetailPage() {
  const { slug } = useParams()
  const add = useAddToCart()

  const [product, setProduct] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [notFound, setNotFound] = useState(false)

  const [qty, setQty] = useState(1)
  const [feedback, setFeedback] = useState(null) // { ok:bool, message:string }
  const [adding, setAdding] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    setNotFound(false)
    try {
      const data = await fetchProduct(slug)
      setProduct(data)
    } catch (err) {
      if (err.response?.status === 404) setNotFound(true)
      else setError('Could not load this product. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [slug])

  useEffect(() => { load() }, [load])

  async function handleAdd() {
    setAdding(true)
    setFeedback(null)
    const res = await add(product, qty)
    if (res.status === 'ok') setFeedback({ ok: true, message: 'Added to your cart.' })
    else if (res.status === 'error') setFeedback({ ok: false, message: res.message })
    setAdding(false)
  }

  if (loading) return <div className="container page"><Loader /></div>
  if (notFound) return (
    <div className="container page empty-state">
      <h1 className="section-title">Product not found</h1>
      <p>It may have been removed. <Link to="/products">Back to products</Link></p>
    </div>
  )
  if (error) return <div className="container page"><ErrorMessage message={error} onRetry={load} /></div>
  if (!product) return null

  const { name, price, description, image, stock, is_available, category_detail } = product
  const imgUrl = resolveMediaUrl(image)
  const outOfStock = is_available === false || stock === 0

  return (
    <div className="container">
      <p style={{ margin: 'var(--space-4) 0' }}>
        <Link to="/products" className="navbar-link">← Back to products</Link>
      </p>
      <div className="detail">
        <div className="detail-img">
          {imgUrl ? <img src={imgUrl} alt={name} /> : <span>{name.charAt(0)}</span>}
        </div>
        <div className="detail-info">
          {category_detail && <span className="badge">{category_detail.name}</span>}
          <h1>{name}</h1>
          <span className={`stock-badge ${outOfStock ? 'out' : 'in'}`}>
            {outOfStock ? 'Out of stock' : `In stock (${stock} available)`}
          </span>
          <div className="detail-price">${price}</div>
          <p className="detail-desc">{description}</p>

          {!outOfStock && (
            <div className="qty-row">
              <label htmlFor="qty">Qty</label>
              <input
                id="qty" type="number" min="1" max={stock} value={qty}
                onChange={(e) => setQty(Math.max(1, Math.min(stock, Number(e.target.value) || 1)))}
              />
            </div>
          )}

          <button
            className="btn btn-primary"
            onClick={handleAdd}
            disabled={outOfStock || adding}
          >
            {outOfStock ? 'Out of stock' : adding ? 'Adding…' : 'Add to Cart'}
          </button>

          {feedback && (
            <div className={`add-feedback ${feedback.ok ? 'ok' : 'err'}`}>
              {feedback.message}
              {feedback.ok && <> <Link to="/cart">View cart →</Link></>}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
