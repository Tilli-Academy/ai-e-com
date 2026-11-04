/*
 * Small pure helpers for the chat widget.
 */

// Show a "Log in" prompt when an anonymous user asked about orders (the backend
// replies with a login message for that case).
export function shouldPromptLogin(intent, isAuthenticated) {
  return intent === 'order_status' && !isAuthenticated
}
