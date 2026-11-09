export function ErrorBanner({ message, onRetry }) {
  return (
    <div className="error-banner" role="alert">
      <span>{message}</span>
      {onRetry && <button onClick={onRetry}>Reintentar</button>}
    </div>
  )
}

export function WarningBanner({ message }) {
  return (
    <div className="warning-banner" role="status">
      <span>{message}</span>
    </div>
  )
}
