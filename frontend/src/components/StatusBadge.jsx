/* StatusBadge — coloured pill for an order status (display-only). */
import { statusMeta } from '../utils/orderStatus'

export default function StatusBadge({ status }) {
  const { label, className } = statusMeta(status)
  return <span className={`status-badge ${className}`}>{label}</span>
}
