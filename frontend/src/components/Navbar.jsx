/*
 * Navbar — sticky top navigation shown on every page.
 *
 * - Brand links home.
 * - Search box submits to /products?search=... (listing page reads it in 6.3).
 * - Cart icon shows a live item-count badge (from CartContext).
 * - Auth area shows Login/Register when logged out, or the user's name + a
 *   Logout button when logged in.
 */
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useCart } from '../context/CartContext'

export default function Navbar() {
  const { isAuthenticated, user, logout } = useAuth()
  const { itemCount } = useCart()
  const [term, setTerm] = useState('')
  const navigate = useNavigate()

  function handleSearch(e) {
    e.preventDefault()
    const q = term.trim()
    navigate(q ? `/products?search=${encodeURIComponent(q)}` : '/products')
  }

  function handleLogout() {
    logout()
    navigate('/')
  }

  return (
    <nav className="navbar">
      <div className="container navbar-inner">
        <Link to="/" className="navbar-brand">Shop<span>AI</span></Link>

        <form className="navbar-search" onSubmit={handleSearch}>
          <input
            type="search"
            placeholder="Search products…"
            value={term}
            onChange={(e) => setTerm(e.target.value)}
            aria-label="Search products"
          />
        </form>

        <div className="navbar-links">
          <Link to="/products" className="navbar-link">Products</Link>
          <Link to="/cart" className="navbar-link cart-icon">
            Cart
            {itemCount > 0 && <span className="cart-count">{itemCount}</span>}
          </Link>
          {isAuthenticated ? (
            <>
              <Link to="/orders" className="navbar-link">Orders</Link>
              <span className="navbar-link">Hi, {user.first_name || user.email}</span>
              <button className="btn btn-outline" onClick={handleLogout}>Logout</button>
            </>
          ) : (
            <>
              <Link to="/login" className="navbar-link">Login</Link>
              <Link to="/register" className="btn btn-primary">Sign up</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
