/* Reusable error banner with an optional Retry button. */
export default function ErrorMessage({ message, onRetry }) {
  return (
    <div className="alert" role="alert">
      <span>{message || 'Something went wrong.'}</span>
      {onRetry && (
        <button className="btn btn-outline" onClick={onRetry}>Retry</button>
      )}
    </div>
  )
}
