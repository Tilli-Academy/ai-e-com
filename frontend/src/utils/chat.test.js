import { describe, expect, it } from 'vitest'
import { shouldPromptLogin } from './chat'

describe('shouldPromptLogin', () => {
  it('prompts login only for anonymous order-status replies', () => {
    expect(shouldPromptLogin('order_status', false)).toBe(true)
    expect(shouldPromptLogin('order_status', true)).toBe(false)
    expect(shouldPromptLogin('faq', false)).toBe(false)
    expect(shouldPromptLogin('product', false)).toBe(false)
    expect(shouldPromptLogin('recommendation', false)).toBe(false)
  })
})
