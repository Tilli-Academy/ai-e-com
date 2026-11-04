/*
 * RegisterPage — create an account, then auto-sign-in.
 *
 * The backend's /register/ returns NO tokens, so on a successful 201 we call
 * /login/ with the same credentials to obtain tokens, then redirect home. Shows
 * DRF validation errors per field (email exists, weak password, password
 * mismatch) and any non-field error.
 */
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { loginUser, registerUser } from '../api/auth'
import { parseApiError } from '../api/errors'
import { useAuth } from '../context/AuthContext'
import ErrorMessage from '../components/ErrorMessage'

export default function RegisterPage() {
  const { login } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({
    first_name: '', last_name: '', email: '', password: '', password2: '',
  })
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
      await registerUser(form)                       // 201, no tokens
      // Auto-login with the same credentials to get tokens.
      const data = await loginUser({ email: form.email, password: form.password })
      login(data)
      navigate('/', { replace: true })
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
        <h1>Create your account</h1>
        <p className="auth-sub">Join ShopAI to start shopping.</p>

        {nonFieldError && <ErrorMessage message={nonFieldError} />}

        <form onSubmit={handleSubmit} noValidate>
          <div className="auth-row">
            <div className="form-group">
              <label className="form-label" htmlFor="first_name">First name</label>
              <input
                id="first_name" name="first_name" type="text" autoComplete="given-name"
                className={`form-input ${fieldErrors.first_name ? 'has-error' : ''}`}
                value={form.first_name} onChange={update}
              />
              {fieldErrors.first_name && <div className="field-error">{fieldErrors.first_name}</div>}
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="last_name">Last name</label>
              <input
                id="last_name" name="last_name" type="text" autoComplete="family-name"
                className={`form-input ${fieldErrors.last_name ? 'has-error' : ''}`}
                value={form.last_name} onChange={update}
              />
              {fieldErrors.last_name && <div className="field-error">{fieldErrors.last_name}</div>}
            </div>
          </div>

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
              id="password" name="password" type="password" autoComplete="new-password"
              className={`form-input ${fieldErrors.password ? 'has-error' : ''}`}
              value={form.password} onChange={update} required
            />
            {fieldErrors.password && <div className="field-error">{fieldErrors.password}</div>}
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password2">Confirm password</label>
            <input
              id="password2" name="password2" type="password" autoComplete="new-password"
              className={`form-input ${fieldErrors.password2 ? 'has-error' : ''}`}
              value={form.password2} onChange={update} required
            />
            {fieldErrors.password2 && <div className="field-error">{fieldErrors.password2}</div>}
          </div>

          <button className="btn btn-primary btn-block" type="submit" disabled={loading}>
            {loading ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <p className="auth-switch">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
