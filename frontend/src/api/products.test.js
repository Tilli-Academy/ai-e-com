/*
 * Unit tests for buildProductQuery — ensures the product-list query string is
 * built from UI state without sending empty/noise params.
 */
import { describe, expect, it } from 'vitest'
import { buildProductQuery } from './products'

describe('buildProductQuery', () => {
  it('drops empty values', () => {
    expect(buildProductQuery({ search: '', category: '', ordering: '', page: 1 })).toEqual({})
  })

  it('includes non-empty search, category and ordering', () => {
    expect(buildProductQuery({ search: 'laptop', category: '2', ordering: 'price' }))
      .toEqual({ search: 'laptop', category: '2', ordering: 'price' })
  })

  it('omits page 1 but includes later pages', () => {
    expect(buildProductQuery({ page: 1 })).toEqual({})
    expect(buildProductQuery({ page: 3 })).toEqual({ page: 3 })
  })

  it('handles being called with no arguments', () => {
    expect(buildProductQuery()).toEqual({})
  })
})
