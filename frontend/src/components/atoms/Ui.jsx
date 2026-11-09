import { Database, LoaderCircle, X } from 'lucide-react'

export function Button({ children, variant = 'primary', className = '', ...props }) {
  return (
    <button className={`button ${variant} ${className}`.trim()} {...props}>
      {children}
    </button>
  )
}

export function IconButton({ label, children, ...props }) {
  return (
    <button type="button" className="icon-button" aria-label={label} title={label} {...props}>
      {children || <X size={19} />}
    </button>
  )
}

export function Field({ label, children, ...props }) {
  return (
    <label className="field" {...props}>
      <span>{label}</span>
      {children}
    </label>
  )
}

export function StatCard({ label, value, detail, tone, icon: Icon }) {
  return (
    <article className={`stat-card ${tone}`}>
      <div className="stat-icon">
        <Icon size={19} strokeWidth={2.2} />
      </div>
      <div>
        <p>{label}</p>
        <strong>{value}</strong>
        <small>{detail}</small>
      </div>
    </article>
  )
}

export function LoadingState() {
  return (
    <div className="loading-state" role="status" aria-live="polite">
      <LoaderCircle className="spin" size={24} />
      <span>Cargando información...</span>
    </div>
  )
}

export function EmptyState({ label }) {
  return (
    <div className="empty-state">
      <Database size={25} />
      <span>{label}</span>
    </div>
  )
}
