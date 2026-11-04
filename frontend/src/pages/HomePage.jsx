/*
 * HomePage — landing page.
 *
 * Shows a hero banner and a grid of "featured" products pulled live from the
 * Django API (the first page of /api/products/). Demonstrates the three states
 * every data page should handle: loading, error (with retry), and loaded.
 */
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchProducts } from '../api/products'
import { fetchRecommendations } from '../api/assistant'
import { useAddToCart } from '../hooks/useAddToCart'
import ProductCard from '../components/ProductCard'
import Loader from '../components/Loader'
import ErrorMessage from '../components/ErrorMessage'

export default function HomePage() {
  const add = useAddToCart()
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // "Recommended for You" (backend rule-based recommender; separate state so a
  // failure here never blocks the featured products).
  const [recs, setRecs] = useState([])
  const [recsLoading, setRecsLoading] = useState(true)
  const [recsError, setRecsError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      // Newest 8 products as "featured".
      const data = await fetchProducts({ ordering: '-created_at' })
      setProducts(data.results.slice(0, 8))
    } catch (err) {
      setError('Could not load products. Is the backend running on port 8001?')
    } finally {
      setLoading(false)
    }
  }, [])

  const loadRecs = useCallback(async () => {
    setRecsLoading(true)
    setRecsError(null)
    try {
      setRecs(await fetchRecommendations())
    } catch (err) {
      setRecsError('Could not load recommendations.')
    } finally {
      setRecsLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])
  useEffect(() => { loadRecs() }, [loadRecs])

  return (
    <div className="container">
      {/* Hero */}
      <section className="hero">
        <h1>Shop smarter with ShopAI</h1>
        <p>
          Discover quality products at great prices. Browse the catalog, add to
          your cart, and check out in seconds.
        </p>
        <Link to="/products" className="btn">Browse products</Link>
      </section>

      {/* Recommended for You */}
      <section className="page">
        <h2 className="section-title">Recommended for You</h2>
        {recsLoading && <Loader />}
        {recsError && <ErrorMessage message={recsError} onRetry={loadRecs} />}
        {!recsLoading && !recsError && (
          recs.length === 0
            ? <p className="empty-state">No recommendations available right now. <Link to="/products">Browse all products</Link>.</p>
            : (
              <div className="product-grid">
                {recs.map((p) => <ProductCard key={p.id} product={p} onAddToCart={add} />)}
              </div>
            )
        )}
      </section>

      {/* Featured products */}
      <section className="page">
        <h2 className="section-title">Featured products</h2>
        {loading && <Loader />}
        {error && <ErrorMessage message={error} onRetry={load} />}
        {!loading && !error && (
          products.length === 0
            ? <p>No products available yet.</p>
            : (
              <div className="product-grid">
                {products.map((p) => <ProductCard key={p.id} product={p} onAddToCart={add} />)}
              </div>
            )
        )}
      </section>
    </div>
  )
}
