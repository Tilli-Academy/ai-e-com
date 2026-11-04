/*
 * parseApiError — turn an Axios error from the Django REST API into something
 * the UI can render.
 *
 * DRF returns errors in a few shapes:
 *   - field errors:     { email: ["...exists."], password: ["too short"] }
 *   - non-field detail: { detail: "No active account found..." }
 *   - non_field_errors: { non_field_errors: ["..."] }
 * Network/unknown errors have no response body.
 *
 * Returns: { fieldErrors: { [field]: "message" }, nonFieldError: string|null }
 */
export function parseApiError(error) {
  const result = { fieldErrors: {}, nonFieldError: null }

  // No response => network error / server down.
  if (!error || !error.response) {
    result.nonFieldError =
      'Cannot reach the server. Check your connection and try again.'
    return result
  }

  const data = error.response.data

  // A plain string body.
  if (typeof data === 'string') {
    result.nonFieldError = data
    return result
  }

  if (data && typeof data === 'object') {
    for (const [key, value] of Object.entries(data)) {
      // DRF wraps messages in arrays; take the first for display.
      const message = Array.isArray(value) ? value[0] : String(value)
      if (key === 'detail' || key === 'non_field_errors') {
        result.nonFieldError = message
      } else {
        result.fieldErrors[key] = message
      }
    }
  }

  // Fallback if nothing was extracted.
  if (!result.nonFieldError && Object.keys(result.fieldErrors).length === 0) {
    result.nonFieldError = 'Something went wrong. Please try again.'
  }
  return result
}
