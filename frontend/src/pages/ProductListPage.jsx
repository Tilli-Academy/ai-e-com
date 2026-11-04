/*
 * ProductListPage — the catalog browse page.
 *
 * All filter state lives in the URL query string (?search=&category=&ordering=
 * &page=) via useSearchParams, so the navbar search works, the back button
 * works, and views are shareable. Fetches products + categories from the API
 * and renders loading / error / empty states.
 */
import { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { buildProductQuery, fetchCategories, fetchProducts } from '../api/products'
import { useAddToCart } from '../hooks/useAddToCart'
import ProductCard from '../components/ProductCard'
import Loader from '../components/Loader'
import ErrorMessage from '../components/ErrorMessage'

const PAGE_SIZE = 12   // matches backend REST_FRAMEWORK PAGE_SIZE

export default function ProductListPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const add = useAddToCart()

  const search = searchParams.get('search') || ''
  const category = searchParams.get('category') || ''
  const ordering = searchParams.get('ordering') || ''
  const page = parseInt(searchParams.get('page') || '1', 10)

  const [searchInput, setSearchInput] = useState(search)
  const [categories, setCategories] = useState([])
  const [data, setData] = useState(null)       // { count, next, previous, results }
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Categories once.
  useEffect(() => {
    fetchCategories().then((d) => setCategories(d.results || [])).catch(() => {})
  }, [])

  // Keep the search box in sync if the URL changes (e.g. navbar search).
  useEffect(() => { setSearchInput(search) }, [search])

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const query = buildProductQuery({ search, category, ordering, page })
      const result = await fetchProducts(query)
      setData(result)
    } catch {
      setError('Could not load products. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [search, category, ordering, page])

  useEffect(() => { load() }, [load])

  // --- helpers to update the URL (reset to page 1 on filter changes) ---
  function updateParam(key, value) {
    const next = new URLSearchParams(searchParams)
    if (value) next.set(key, value)
    else next.delete(key)
    next.delete('page')
    setSearchParams(next)
  }
  function submitSearch(e) {
    e.preventDefault()
    updateParam('search', searchInput.trim())
  }
  function goToPage(p) {
    const next = new URLSearchParams(searchParams)
    if (p > 1) next.set('page', p); else next.delete('page')
    setSearchParams(next)
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1

  return (
    <div className="container page">
      <h1 className="section-title">Products</h1>

      {/* Toolbar: search + category + sort */}
      <div className="toolbar">
        <form className="toolbar-search" onSubmit={submitSearch}>
          <input
            type="search"
            placeholder="Search products by name…"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            aria-label="Search products"
            style={{ width: '100%' }}
          />
        </form>

        <select value={category} onChange={(e) => updateParam('category', e.target.value)} aria-label="Filter by category">
          <option value="">All categories</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>

        <select value={ordering} onChange={(e) => updateParam('ordering', e.target.value)} aria-label="Sort products">
          <option value="">Newest</option>
          <option value="price">Price: low to high</option>
          <option value="-price">Price: high to low</option>
          <option value="name">Name: A–Z</option>
        </select>
      </div>

      {loading && <Loader />}
      {error && <ErrorMessage message={error} onRetry={load} />}

      {!loading && !error && data && (
        data.results.length === 0 ? (
          <div className="empty-state">
            <p>No products found{search ? ` for “${search}”` : ''}.</p>
          </div>
        ) : (
          <>
            <p className="result-count">{data.count} product{data.count !== 1 ? 's' : ''} found</p>
            <div className="product-grid">
              {data.results.map((p) => (
                <ProductCard key={p.id} product={p} onAddToCart={add} />
              ))}
            </div>

            {totalPages > 1 && (
              <div className="pagination">
                <button className="btn btn-outline" disabled={!data.previous} onClick={() => goToPage(page - 1)}>
                  ← Prev
                </button>
                <span>Page {page} of {totalPages}</span>
                <button className="btn btn-outline" disabled={!data.next} onClick={() => goToPage(page + 1)}>
                  Next →
                </button>
              </div>
            )}
          </>
        )
      )}
    </div>
  )
}
