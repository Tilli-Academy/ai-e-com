/*
 * ProductCard — reusable catalog tile (home + listing).
 *
 * Shows image (or an initial-letter placeholder), category, name, price, and a
 * stock-availability badge. The "Add to Cart" button is disabled when the item
 * is unavailable or out of stock, and gives inline feedback via the async
 * `onAddToCart(product)` callback (returns {status}). Without the callback the
 * whole card just links to the product detail page.
 */
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { resolveMediaUrl } from '../api/media'

export default function ProductCard({ product, onAddToCart }) {
  const navigate = useNavigate()
  const { name, slug, price, image, category_detail, is_available, stock } = product
  const imgUrl = resolveMediaUrl(image)
  const outOfStock = is_available === false || stock === 0
  const [state, setState] = useState('idle') // idle | adding | added | error

  async function handleAdd(e) {
    e.preventDefault()
    if (!onAddToCart) { navigate(`/products/${slug}`); return }
    setState('adding')
    const res = await onAddToCart(product)
    if (res?.status === 'ok') {
      setState('added')
      setTimeout(() => setState('idle'), 1500)
    } else if (res?.status === 'error') {
      setState('error')
      setTimeout(() => setState('idle'), 2000)
    } else {
      setState('idle') // 'auth' -> navigated away
    }
  }

  const label = outOfStock
    ? 'Out of stock'
    : state === 'adding' ? 'Adding…'
    : state === 'added' ? 'Added ✓'
    : state === 'error' ? 'Try again'
    : 'Add to Cart'

  return (
    <div className="product-card">
      <Link to={`/products/${slug}`} className="product-card-img">
        {imgUrl ? <img src={imgUrl} alt={name} /> : <span>{name.charAt(0)}</span>}
      </Link>
      <div className="product-card-body">
        {category_detail && <span className="product-card-cat">{category_detail.name}</span>}
        <Link to={`/products/${slug}`} className="product-card-name">{name}</Link>
        <span className={`stock-badge ${outOfStock ? 'out' : 'in'}`}>
          {outOfStock ? 'Out of stock' : `In stock (${stock})`}
        </span>
        <span className="product-card-price">${price}</span>
      </div>
      <div className="product-card-footer">
        <button
          className="btn btn-primary btn-block"
          onClick={handleAdd}
          disabled={outOfStock || state === 'adding'}
        >
          {label}
        </button>
      </div>
    </div>
  )
}
