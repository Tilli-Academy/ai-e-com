/*
 * Application entry point. Mounts <App> into index.html's #root, wrapped in:
 *   - BrowserRouter  : client-side routing
 *   - AuthProvider   : logged-in user + tokens
 *   - CartProvider   : cart item count / actions
 * and loads the global design-system stylesheet.
 */
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { AuthProvider } from './context/AuthContext'
import { CartProvider } from './context/CartContext'
import './styles/index.css'

// When served under the IDE proxy, the app lives at "/proxy/3002/". React
// Router needs that as its basename so <Link>s and navigation produce correct
// URLs. BASE_URL is "/" in a normal setup, giving basename "" (root). We strip
// the trailing slash because React Router expects a basename without one.
const basename = import.meta.env.BASE_URL.replace(/\/$/, '')

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter basename={basename}>
      <AuthProvider>
        <CartProvider>
          <App />
        </CartProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
