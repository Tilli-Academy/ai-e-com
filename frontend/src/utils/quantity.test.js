import { describe, expect, it } from 'vitest'
import { clampQuantity } from './quantity'

describe('clampQuantity', () => {
  it('keeps a value within range', () => {
    expect(clampQuantity(3, 10)).toBe(3)
  })
  it('clamps above max', () => {
    expect(clampQuantity(50, 8)).toBe(8)
  })
  it('clamps below min (default 1)', () => {
    expect(clampQuantity(0, 10)).toBe(1)
    expect(clampQuantity(-5, 10)).toBe(1)
  })
  it('floors fractional and handles non-numbers', () => {
    expect(clampQuantity(2.9, 10)).toBe(2)
    expect(clampQuantity('abc', 10)).toBe(1)
  })
})
