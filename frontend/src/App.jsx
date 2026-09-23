import { useEffect, useMemo, useRef, useState } from 'react'
import {
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  Check,
  CircleDollarSign,
  ClipboardList,
  Database,
  LayoutDashboard,
  LoaderCircle,
  Mic,
  Plus,
  RefreshCw,
  Search,
  Trash2,
  X,
} from 'lucide-react'

const API = '/api'

const views = [
  { id: 'resumen', label: 'Resumen', icon: LayoutDashboard },
  { id: 'tasks', label: 'Tareas', icon: ClipboardList },
  { id: 'movimientos', label: 'Movimientos', icon: Database },
]

const statusLabels = { todo: 'Pendiente', in_progress: 'En curso', done: 'Completada' }
const statusClass = { todo: 'amber', in_progress: 'blue', done: 'green' }

function formatMoney(value) {
  if (value === null || value === undefined || value === '') return '?'
  const text = String(value).trim()
  if (!text) return '?'
  const normalized = text.replace(/[^0-9.\-]/g, '')
  if (!normalized) return text
  const num = Number(normalized)
  if (!Number.isFinite(num)) return text
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  }).format(num)
}

function formatDate(value) {
  if (!value) return '?'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium' }).format(date)
}

async function request(path, options = {}, signal) {
  const response = await fetch(`${API}${path}`, {
    signal,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  })

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => ({}))
    throw new Error(errorPayload.detail || errorPayload.message || `La solicitud fall? (${response.status})`)
  }

  return response.status === 204 ? null : response.json()
}

async function requestCsv(payload, signal) {
  const response = await fetch(`${API}/movements/export/`, {
    method: 'POST',
    signal,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const errorText = await response.text().catch(() => '')
    throw new Error(errorText || 'No fue posible exportar el detalle.')
  }

  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = 'movimientos.csv'
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  window.URL.revokeObjectURL(url)
}

function StatCard({ label, value, detail, tone, icon: Icon }) {
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

function TaskForm({ task, onClose, onSaved }) {
  const [form, setForm] = useState({
    title: task?.title || '',
    description: task?.description || '',
    status: task?.status || 'todo',
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    if (!form.title.trim()) {
      setError('Escribe un t?tulo para la tarea.')
      return
    }

    setSaving(true)
    setError('')

    try {
      const saved = await request(task ? `/tasks/${task.id}/` : '/tasks/', {
        method: task ? 'PATCH' : 'POST',
        body: JSON.stringify(form),
      })
      onSaved(saved)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <form className="modal" onSubmit={handleSubmit}>
        <div className="modal-heading">
          <div>
            <span className="eyebrow">Gesti?n operativa</span>
            <h2>{task ? 'Editar tarea' : 'Nueva tarea'}</h2>
          </div>
          <button type="button" className="icon-button" onClick={onClose} aria-label="Cerrar">
            <X size={19} />
          </button>
        </div>

        <label>
          T?tulo
          <input
            autoFocus
            value={form.title}
            onChange={(event) => setForm({ ...form, title: event.target.value })}
            placeholder="Ej. Revisar conciliaci?n"
          />
        </label>

        <label>
          Descripci?n
          <textarea
            rows="4"
            value={form.description}
            onChange={(event) => setForm({ ...form, description: event.target.value })}
            placeholder="Agrega contexto para el equipo"
          />
        </label>

        <label>
          Estado
          <select value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}>
            <option value="todo">Pendiente</option>
            <option value="in_progress">En curso</option>
            <option value="done">Completada</option>
          </select>
        </label>

        {error && <p className="form-error">{error}</p>}

        <div className="modal-actions">
          <button type="button" className="button secondary" onClick={onClose}>Cancelar</button>
          <button className="button primary" disabled={saving}>
            {saving ? <LoaderCircle className="spin" size={17} /> : <Check size={17} />}
            {task ? 'Guardar cambios' : 'Crear tarea'}
          </button>
        </div>
      </form>
    </div>
  )
}

function TasksView({ onCountChange }) {
  const [tasks, setTasks] = useState([])
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState(null)

  async function loadTasks() {
    setLoading(true)
    setError('')
    try {
      const data = await request('/tasks/')
      setTasks(data)
      onCountChange(data.length)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadTasks()
  }, [])

  const filtered = tasks.filter((task) => `${task.title} ${task.description}`.toLowerCase().includes(query.toLowerCase()))

  async function removeTask(task) {
    if (!window.confirm(`?Eliminar "${task.title}"?`)) return
    try {
      await request(`/tasks/${task.id}/`, { method: 'DELETE' })
      const nextTasks = tasks.filter((item) => item.id !== task.id)
      setTasks(nextTasks)
      onCountChange(nextTasks.length)
    } catch (requestError) {
      setError(requestError.message)
    }
  }

  function savedTask(saved) {
    setTasks((current) => {
      const exists = current.some((item) => item.id === saved.id)
      const next = exists ? current.map((item) => (item.id === saved.id ? saved : item)) : [saved, ...current]
      onCountChange(next.length)
      return next
    })
    setEditing(null)
  }

  return (
    <section className="content-section">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Seguimiento del equipo</span>
          <h2>Tareas</h2>
          <p>Convierte pendientes en avances visibles.</p>
        </div>
        <button className="button primary" onClick={() => setEditing({})}>
          <Plus size={17} />
          Nueva tarea
        </button>
      </div>

      <div className="toolbar">
        <div className="search-box">
          <Search size={17} />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar tareas..." />
        </div>
        <button className="button ghost" onClick={loadTasks}>
          <RefreshCw size={16} />
          Actualizar
        </button>
      </div>

      {error && <ErrorBanner message={error} onRetry={loadTasks} />}
      {loading ? (
        <LoadingState />
      ) : filtered.length === 0 ? (
        <EmptyState label="No hay tareas que mostrar" />
      ) : (
        <div className="task-list">
          {filtered.map((task) => (
            <article className="task-row" key={task.id}>
              <div className="task-check">{task.status === 'done' && <Check size={15} />}</div>
              <div className="task-main">
                <h3>{task.title}</h3>
                <p>{task.description || 'Sin descripci?n'}</p>
                <small>Actualizada {formatDate(task.updated_at)}</small>
              </div>

              <span className={`status-pill ${statusClass[task.status] || 'gray'}`}>
                {statusLabels[task.status] || task.status}
              </span>

              <div className="row-actions">
                <button className="text-button" onClick={() => setEditing(task)}>Editar</button>
                <button className="danger-button" onClick={() => removeTask(task)} aria-label={`Eliminar ${task.title}`}>
                  <Trash2 size={16} />
                </button>
              </div>
            </article>
          ))}
        </div>
      )}

      {editing && <TaskForm task={editing.id ? editing : null} onClose={() => setEditing(null)} onSaved={savedTask} />}
    </section>
  )
}

function ErrorBanner({ message, onRetry }) {
  return (
    <div className="error-banner">
      <span>{message}</span>
      <button onClick={onRetry}>Reintentar</button>
    </div>
  )
}

function LoadingState() {
  return (
    <div className="loading-state">
      <LoaderCircle className="spin" size={24} />
      <span>Cargando informaci?n...</span>
    </div>
  )
}

function EmptyState({ label }) {
  return (
    <div className="empty-state">
      <Database size={25} />
      <span>{label}</span>
    </div>
  )
}

function MovementView() {
  const [form, setForm] = useState({
    date_type: 'ACCOUNTING_DATE',
    date_from: '2026-08-01',
    date_to: '2026-08-31',
    initial_rubro: 110000,
    final_rubro: 199999,
    customer_account: '',
    nit: '',
    branch: '',
    page: 1,
    page_size: 50,
    sorting: [{ field: 'accounting_date', direction: 'asc' }],
  })

  const [rows, setRows] = useState([])
  const [columns, setColumns] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [summary, setSummary] = useState(null)
  const [warnings, setWarnings] = useState([])
  const abortRef = useRef(null)

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  function resetForm() {
    setForm({
      date_type: 'ACCOUNTING_DATE',
      date_from: '2026-08-01',
      date_to: '2026-08-31',
      initial_rubro: 110000,
      final_rubro: 199999,
      customer_account: '',
      nit: '',
      branch: '',
      page: 1,
      page_size: 50,
      sorting: [{ field: 'accounting_date', direction: 'asc' }],
    })
    setError('')
    setWarnings([])
  }

  async function submitQuery(nextPage = 1) {
    const payload = {
      ...form,
      page: Number(nextPage || 1),
      customer_account: form.customer_account === '' ? null : Number(form.customer_account),
      nit: form.nit === '' ? null : form.nit,
      branch: form.branch === '' ? null : Number(form.branch),
      initial_rubro: Number(form.initial_rubro),
      final_rubro: Number(form.final_rubro),
      page_size: Number(form.page_size),
    }

    if (!payload.date_type || !payload.date_from || !payload.date_to || !payload.initial_rubro || !payload.final_rubro) {
      setError('Completa el tipo de fecha, el rango de fechas y los rubros.')
      return
    }

    if (payload.initial_rubro > payload.final_rubro) {
      setError('El rubro inicial no puede ser mayor que el rubro final.')
      return
    }

    if (abortRef.current) abortRef.current.abort()
    const controller = new AbortController()
    abortRef.current = controller
    setLoading(true)
    setError('')

    try {
      const result = await request('/movements/query/', {
        method: 'POST',
        body: JSON.stringify(payload),
      }, controller.signal)
      setColumns(result.columns || [])
      setRows(result.rows || [])
      setSummary(result.summary || null)
      setWarnings(result.warnings || [])
    } catch (requestError) {
      if (requestError.name === 'AbortError') return
      setError(requestError.message)
    } finally {
      setLoading(false)
    }
  }

  async function exportCsv() {
    const payload = {
      ...form,
      customer_account: form.customer_account === '' ? null : Number(form.customer_account),
      nit: form.nit === '' ? null : form.nit,
      branch: form.branch === '' ? null : Number(form.branch),
      initial_rubro: Number(form.initial_rubro),
      final_rubro: Number(form.final_rubro),
      page_size: Number(form.page_size),
    }

    if (abortRef.current) abortRef.current.abort()
    const controller = new AbortController()
    abortRef.current = controller

    try {
      await requestCsv(payload, controller.signal)
    } catch (requestError) {
      setError(requestError.message)
    }
  }

  const activeFilters = useMemo(() => {
    const list = []
    list.push(form.date_type === 'ACCOUNTING_DATE' ? 'Fecha contable' : 'Fecha valor contable')
    list.push(`${form.date_from} a ${form.date_to}`)
    list.push(`Rubro ${form.initial_rubro} a ${form.final_rubro}`)
    if (form.customer_account) list.push(`Cuenta ${form.customer_account}`)
    if (form.nit) list.push(`NIT ${form.nit}`)
    if (form.branch) list.push(`Sucursal ${form.branch}`)
    return list.join(' ? ')
  }, [form])

  return (
    <section className="content-section">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Detalle financiero</span>
          <h2>Movimientos</h2>
          <p>Consulta controlada del detalle por rango y fechas.</p>
        </div>

        <div className="toolbar compact">
          <button type="button" className="button secondary" onClick={resetForm}>Limpiar</button>
          <button type="button" className="button primary" onClick={() => submitQuery(1)} disabled={loading}>
            {loading ? <LoaderCircle className="spin" size={16} /> : <Search size={16} />}
            Consultar
          </button>
        </div>
      </div>

      <div className="movement-form" style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', marginBottom: '1.5rem' }}>
        <div className="segment" style={{ gridColumn: '1 / -1' }}>
          <label style={{ fontSize: '11px', fontWeight: 700, color: '#52675e' }}>Tipo de fecha</label>
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem', flexWrap: 'wrap' }}>
            <button
              type="button"
              className={form.date_type === 'ACCOUNTING_DATE' ? 'button primary' : 'button secondary'}
              onClick={() => updateField('date_type', 'ACCOUNTING_DATE')}
            >
              Fecha contable
            </button>
            <button
              type="button"
              className={form.date_type === 'ACCOUNTING_VALUE_DATE' ? 'button primary' : 'button secondary'}
              onClick={() => updateField('date_type', 'ACCOUNTING_VALUE_DATE')}
            >
              Fecha valor contable
            </button>
          </div>
        </div>

        <label>
          Fecha inicial
          <input type="date" value={form.date_from} onChange={(event) => updateField('date_from', event.target.value)} />
        </label>

        <label>
          Fecha final
          <input type="date" value={form.date_to} onChange={(event) => updateField('date_to', event.target.value)} />
        </label>

        <label>
          Rubro inicial
          <input type="number" min="0" value={form.initial_rubro} onChange={(event) => updateField('initial_rubro', event.target.value)} />
        </label>

        <label>
          Rubro final
          <input type="number" min="0" value={form.final_rubro} onChange={(event) => updateField('final_rubro', event.target.value)} />
        </label>

        <label>
          Cuenta cliente
          <input type="number" value={form.customer_account} onChange={(event) => updateField('customer_account', event.target.value)} />
        </label>

        <label>
          NIT
          <input value={form.nit} onChange={(event) => updateField('nit', event.target.value)} />
        </label>

        <label>
          Sucursal
          <input type="number" value={form.branch} onChange={(event) => updateField('branch', event.target.value)} />
        </label>

        <label>
          P?gina
          <input type="number" min="1" value={form.page} onChange={(event) => updateField('page', Number(event.target.value || 1))} />
        </label>

        <label>
          Tama?o p?gina
          <input type="number" min="1" max="100" value={form.page_size} onChange={(event) => updateField('page_size', Number(event.target.value || 1))} />
        </label>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'end', flexWrap: 'wrap' }}>
          <button type="button" className="button primary" onClick={() => submitQuery(form.page)} disabled={loading}>
            {loading ? 'Consultando...' : 'Consultar'}
          </button>
          <button type="button" className="button secondary" onClick={exportCsv}>Exportar CSV</button>
          <button type="button" className="button ghost" aria-label="Reconocer voz" title="Reconocimiento de voz (opcional)">
            <Mic size={16} />
          </button>
        </div>
      </div>

      {error && <div className="error-banner"><span>{error}</span></div>}
      {warnings.length > 0 && <div className="warning-banner"><span>{warnings.join(' ')}</span></div>}
      <div className="summary-strip" style={{ marginBottom: '1rem' }}>
        <strong>Filtros activos:</strong> {activeFilters}
      </div>

      {summary && (
        <div className="summary-strip" style={{ marginBottom: '1rem' }}>
          <strong>Resumen:</strong> {summary.movement_count_on_page} filas ? {summary.date_from} a {summary.date_to}
        </div>
      )}

      {loading ? (
        <LoadingState />
      ) : rows.length === 0 ? (
        <EmptyState label="Sin resultados para el rango solicitado" />
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {columns.map((column) => (
                  <th key={column.key}>{column.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, rowIndex) => (
                <tr key={`${row.rubro ?? rowIndex}-${row.accounting_date ?? rowIndex}-${rowIndex}`}>
                  {columns.map((column) => {
                    const value = row[column.key]
                    let display = value ?? '?'

                    if (column.key === 'amount' && value !== null && value !== undefined) {
                      display = formatMoney(value)
                    }

                    if (column.key === 'accounting_date' || column.key === 'accounting_value_date') {
                      display = formatDate(value)
                    }

                    if (column.key === 'operation_type') {
                      display = value === 'DEBIT' ? 'D?bito' : value === 'CREDIT' ? 'Cr?dito' : 'Desconocido'
                    }

                    return (
                      <td key={`${column.key}-${rowIndex}`} title={String(value ?? '')}>
                        {display}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

function Dashboard({ onNavigate, taskCount }) {
  return (
    <section className="content-section dashboard">
      <div className="welcome-panel">
        <div>
          <span className="eyebrow">Martes, 8 de septiembre de 2026</span>
          <h2>Tu operaci?n, en una sola vista.</h2>
          <p>Revisa el trabajo del equipo y consulta el detalle financiero del d?a.</p>
        </div>
        <div className="welcome-orbit">
          <BarChart3 size={68} strokeWidth={1.1} />
        </div>
      </div>

      <div className="stats-grid">
        <StatCard label="Tareas activas" value={taskCount || '?'} detail="En tu espacio de trabajo" tone="mint" icon={ClipboardList} />
        <StatCard label="Detalle" value="Movimientos" detail="Consulta controlada" tone="coral" icon={ArrowUpRight} />
        <StatCard label="Exportaci?n" value="CSV" detail="Detallado y seguro" tone="sun" icon={ArrowDownRight} />
      </div>

      <div className="quick-section">
        <div className="section-heading compact">
          <div>
            <span className="eyebrow">Accesos r?pidos</span>
            <h2>Explora tus datos</h2>
          </div>
        </div>

        <div className="quick-grid">
          <button onClick={() => onNavigate('tasks')}>
            <ClipboardList size={22} />
            <span>
              <strong>Organiza tareas</strong>
              <small>Gestiona el trabajo pendiente</small>
            </span>
            <ArrowUpRight size={17} />
          </button>

          <button onClick={() => onNavigate('movimientos')}>
            <Database size={22} />
            <span>
              <strong>Detalle financiero</strong>
              <small>Consulta por fechas y rubros</small>
            </span>
            <ArrowUpRight size={17} />
          </button>

          <button onClick={() => onNavigate('movimientos')}>
            <ArrowDownRight size={22} />
            <span>
              <strong>Exporta movimientos</strong>
              <small>CSV con detalles financieros</small>
            </span>
            <ArrowUpRight size={17} />
          </button>
        </div>
      </div>
    </section>
  )
}

export default function App() {
  const [activeView, setActiveView] = useState('resumen')
  const [taskCount, setTaskCount] = useState(0)
  const active = views.find((view) => view.id === activeView)

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <CircleDollarSign size={22} />
          </div>
          <div>
            <strong>financiera</strong>
            <span>Centro operativo</span>
          </div>
        </div>

        <div className="workspace-label">Espacio de trabajo</div>

        <nav>
          {views.map(({ id, label, icon: Icon }) => (
            <button key={id} className={activeView === id ? 'nav-item active' : 'nav-item'} onClick={() => setActiveView(id)}>
              <Icon size={18} />
              <span>{label}</span>
              {id === 'tasks' && taskCount > 0 && <b>{taskCount}</b>}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="profile-dot">JC</div>
          <div>
            <strong>Jairo Ceron</strong>
            <span>Administrador</span>
          </div>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <span className="breadcrumb">Operaciones / {active.label}</span>
            <h1>{activeView === 'resumen' ? 'Buenos d?as, Jairo' : active.label}</h1>
          </div>
          <div className="connection">
            <span />
            API conectada
          </div>
        </header>

        {activeView === 'resumen' ? (
          <Dashboard onNavigate={setActiveView} taskCount={taskCount} />
        ) : activeView === 'tasks' ? (
          <TasksView onCountChange={setTaskCount} />
        ) : (
          <MovementView />
        )}
      </main>
    </div>
  )
}
