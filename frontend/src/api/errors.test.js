/*
 * Unit tests for parseApiError — verifies it maps the real DRF error shapes our
 * Django auth endpoints return into { fieldErrors, nonFieldError }.
 */
import { describe, expect, it } from 'vitest'
import { parseApiError } from './errors'

describe('parseApiError', () => {
  it('maps field errors (register: duplicate email, weak password)', () => {
    const err = {
      response: {
        data: {
          email: ['user with this email address already exists.'],
          password: ['This password is too short.'],
        },
      },
    }
    const { fieldErrors, nonFieldError } = parseApiError(err)
    expect(fieldErrors.email).toBe('user with this email address already exists.')
    expect(fieldErrors.password).toBe('This password is too short.')
    expect(nonFieldError).toBeNull()
  })

  it('maps password confirmation mismatch to the password2 field', () => {
    const err = { response: { data: { password2: ["The two password fields didn't match."] } } }
    const { fieldErrors } = parseApiError(err)
    expect(fieldErrors.password2).toBe("The two password fields didn't match.")
  })

  it('maps "detail" (login: bad credentials) to a non-field error', () => {
    const err = { response: { data: { detail: 'No active account found with the given credentials' } } }
    const { fieldErrors, nonFieldError } = parseApiError(err)
    expect(nonFieldError).toBe('No active account found with the given credentials')
    expect(Object.keys(fieldErrors)).toHaveLength(0)
  })

  it('maps non_field_errors to a non-field error', () => {
    const err = { response: { data: { non_field_errors: ['Something is invalid.'] } } }
    expect(parseApiError(err).nonFieldError).toBe('Something is invalid.')
  })

  it('handles a network error (no response)', () => {
    const { nonFieldError } = parseApiError({ message: 'Network Error' })
    expect(nonFieldError).toMatch(/cannot reach the server/i)
  })
})
