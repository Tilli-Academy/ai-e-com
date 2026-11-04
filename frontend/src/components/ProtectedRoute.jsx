/*
 * ProtectedRoute — wraps pages that require login (cart, checkout, orders).
 * If the user isn't authenticated, redirect to /login and remember where they
 * were headed, so LoginPage can send them back after a successful sign-in.
 */
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth()
  const location = useLocation()

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }
  return children
}
