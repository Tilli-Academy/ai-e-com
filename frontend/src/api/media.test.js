/*
 * Tests for resolveMediaUrl. Vitest reads vite.config.js, so BASE_URL here is
 * the configured base ("/absproxy/3002/"). We assert against it so the test is
 * correct regardless of the base value.
 */
import { describe, expect, it } from 'vitest'
import { resolveMediaUrl } from './media'

const BASE = import.meta.env.BASE_URL   // e.g. "/absproxy/3002/" or "/"

describe('resolveMediaUrl', () => {
  it('returns null for empty/missing image', () => {
    expect(resolveMediaUrl(null)).toBeNull()
    expect(resolveMediaUrl('')).toBeNull()
    expect(resolveMediaUrl(undefined)).toBeNull()
  })

  it('strips scheme+host from an absolute backend URL and prefixes the base', () => {
    expect(resolveMediaUrl('http://127.0.0.1:8001/media/products/x.png'))
      .toBe(`${BASE}media/products/x.png`)
  })

  it('maps an already-relative path onto the base', () => {
    expect(resolveMediaUrl('/media/products/x.png'))
      .toBe(`${BASE}media/products/x.png`)
  })

  it('does not double the base prefix', () => {
    const result = resolveMediaUrl('http://127.0.0.1:8001/media/products/x.png')
    expect(result.startsWith(BASE)).toBe(true)
    expect(result.indexOf('media/products')).toBe(result.lastIndexOf('media/products'))
  })
})
