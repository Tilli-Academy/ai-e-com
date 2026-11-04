/*
 * LoginPage — email + password sign-in.
 *
 * On success: stores tokens/user via AuthContext and returns the user to the
 * page they were trying to reach (ProtectedRoute passes it in location.state),
 * or home. Shows field-level and non-field API errors clearly.
 */
import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { loginUser } from '../api/auth'
import { parseApiError } from '../api/errors'
import { useAuth } from '../context/AuthContext'
import ErrorMessage from '../components/ErrorMessage'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const redirectTo = location.state?.from?.pathname || '/'

  const [form, setForm] = useState({ email: '', password: '' })
  const [fieldErrors, setFieldErrors] = useState({})
  const [nonFieldError, setNonFieldError] = useState(null)
  const [loading, setLoading] = useState(false)

  function update(e) {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setFieldErrors({})
    setNonFieldError(null)
    try {
      const data = await loginUser(form)
      login(data)                 // { access, refresh, user }
      navigate(redirectTo, { replace: true })
    } catch (err) {
      const { fieldErrors, nonFieldError } = parseApiError(err)
      setFieldErrors(fieldErrors)
      setNonFieldError(nonFieldError)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <div className="card auth-wrap">
        <h1>Welcome back</h1>
        <p className="auth-sub">Sign in to your ShopAI account.</p>

        {nonFieldError && <ErrorMessage message={nonFieldError} />}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label className="form-label" htmlFor="email">Email</label>
            <input
              id="email" name="email" type="email" autoComplete="email"
              className={`form-input ${fieldErrors.email ? 'has-error' : ''}`}
              value={form.email} onChange={update} required
            />
            {fieldErrors.email && <div className="field-error">{fieldErrors.email}</div>}
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password">Password</label>
            <input
              id="password" name="password" type="password" autoComplete="current-password"
              className={`form-input ${fieldErrors.password ? 'has-error' : ''}`}
              value={form.password} onChange={update} required
            />
            {fieldErrors.password && <div className="field-error">{fieldErrors.password}</div>}
          </div>

          <button className="btn btn-primary btn-block" type="submit" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <p className="auth-switch">
          New here? <Link to="/register">Create an account</Link>
        </p>
      </div>
    </div>
  )
}
