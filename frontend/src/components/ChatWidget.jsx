/*
 * ChatWidget — floating AI shopping assistant.
 *
 * A fixed button opens a chat panel that talks to POST /api/assistant/chat/
 * (via the shared Axios instance, so the JWT is attached automatically and the
 * call is proxied to Django — the browser never contacts Ollama).
 *
 * Shows user/assistant bubbles, a typing indicator while waiting, authoritative
 * product chips for product/recommendation replies, and a login prompt when an
 * anonymous user asks about orders. Mounted once in App, over every page.
 */
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { sendChatMessage } from '../api/assistant'
import { useAuth } from '../context/AuthContext'
import { shouldPromptLogin } from '../utils/chat'

const WELCOME = {
  role: 'assistant',
  text: "Hi! I'm your ShopAI assistant. Ask me about products, recommendations, " +
        "store FAQs, or your order status.",
}

export default function ChatWidget() {
  const { isAuthenticated } = useAuth()
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([WELCOME])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const scrollRef = useRef(null)
  const idRef = useRef(0)

  const nextId = () => (idRef.current += 1)

  // Auto-scroll to the newest message / typing indicator.
  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }, [messages, loading, open])

  async function handleSend(e) {
    e.preventDefault()
    const text = input.trim()
    if (!text || loading) return

    setMessages((m) => [...m, { id: nextId(), role: 'user', text }])
    setInput('')
    setLoading(true)
    try {
      const data = await sendChatMessage(text)
      setMessages((m) => [...m, {
        id: nextId(),
        role: 'assistant',
        text: data.reply,
        products: data.products || [],
        promptLogin: shouldPromptLogin(data.intent, isAuthenticated),
      }])
    } catch {
      setMessages((m) => [...m, {
        id: nextId(),
        role: 'assistant',
        text: "Sorry, I couldn't reach the assistant right now. Please try again.",
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {/* Floating toggle button */}
      <button
        className="chat-fab"
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? 'Close chat assistant' : 'Open chat assistant'}
      >
        {open ? '✕' : '💬'}
      </button>

      {open && (
        <div className="chat-panel" role="dialog" aria-label="Shopping assistant">
          <div className="chat-header">
            <span>🛍️ ShopAI Assistant</span>
            <button className="chat-close" onClick={() => setOpen(false)} aria-label="Close">✕</button>
          </div>

          <div className="chat-messages" ref={scrollRef}>
            {messages.map((m, i) => (
              <div key={m.id ?? `w${i}`} className={`chat-msg ${m.role}`}>
                <div className="chat-bubble">{m.text}</div>

                {m.products && m.products.length > 0 && (
                  <div className="chat-products">
                    {m.products.map((p) => (
                      <Link key={p.id} to={`/products/${p.slug}`} className="chat-product-chip" onClick={() => setOpen(false)}>
                        <span className="chip-name">{p.name}</span>
                        <span className="chip-price">${p.price}</span>
                      </Link>
                    ))}
                  </div>
                )}

                {m.promptLogin && (
                  <div className="chat-login-hint">
                    <Link to="/login" onClick={() => setOpen(false)}>Log in</Link> to check your orders.
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="chat-msg assistant">
                <div className="chat-bubble chat-typing" aria-label="Assistant is typing">
                  <span></span><span></span><span></span>
                </div>
              </div>
            )}
          </div>

          <form className="chat-input" onSubmit={handleSend}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about products, orders, FAQs…"
              aria-label="Message"
              disabled={loading}
            />
            <button className="btn btn-primary" type="submit" disabled={loading || !input.trim()}>
              Send
            </button>
          </form>
        </div>
      )}
    </>
  )
}
