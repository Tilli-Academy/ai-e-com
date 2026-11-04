/*
 * Order status metadata — maps the backend status values (Order.Status) to a
 * display label and a CSS modifier class for colouring the badge. Display-only;
 * customers never change status here.
 */
export const STATUS_META = {
  pending:    { label: 'Pending',    className: 'status-pending' },
  paid:       { label: 'Paid',       className: 'status-paid' },
  processing: { label: 'Processing', className: 'status-processing' },
  shipped:    { label: 'Shipped',    className: 'status-shipped' },
  delivered:  { label: 'Delivered',  className: 'status-delivered' },
  cancelled:  { label: 'Cancelled',  className: 'status-cancelled' },
}

export function statusMeta(status) {
  return STATUS_META[status] || { label: status || 'Unknown', className: 'status-unknown' }
}
