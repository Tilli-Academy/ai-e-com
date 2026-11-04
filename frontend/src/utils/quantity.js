/*
 * clampQuantity — keep a quantity within [min, max].
 * Used by the cart stepper so the UI never sends an out-of-range quantity
 * (the backend still validates authoritatively).
 */
export function clampQuantity(value, max, min = 1) {
  const n = Number(value)
  if (!Number.isFinite(n)) return min
  return Math.max(min, Math.min(max, Math.trunc(n)))
}
