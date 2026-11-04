import { describe, expect, it } from 'vitest'
import { statusMeta } from './orderStatus'

describe('statusMeta', () => {
  it('maps every known status to a label + class', () => {
    for (const s of ['pending', 'paid', 'processing', 'shipped', 'delivered', 'cancelled']) {
      const m = statusMeta(s)
      expect(m.label.toLowerCase()).toBe(s)
      expect(m.className).toBe(`status-${s}`)
    }
  })

  it('falls back gracefully for an unknown status', () => {
    const m = statusMeta('weird')
    expect(m.label).toBe('weird')
    expect(m.className).toBe('status-unknown')
  })

  it('handles null/undefined', () => {
    expect(statusMeta(undefined).label).toBe('Unknown')
  })
})
