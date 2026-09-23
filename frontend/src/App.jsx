import { useEffect, useMemo, useState } from 'react'
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
  { id: 'ingresos', label: 'Ingresos', icon: ArrowUpRight },
  { id: 'gastos', label: 'Gastos', icon: ArrowDownRight },
]
const statusLabels = { todo: 'Pendiente', in_progress: 'En curso', done: 'Completada' }
const statusClass = { todo: 'amber', in_progress: 'blue', done: 'green' }

function formatMoney(value) {
  const amount = Number(value)
  return Number.isFinite(amount)
    ? new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(amount)
    : value || '—'
}

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium' }).format(date)
}

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || `La solicitud falló (${response.status})`)
  }
  return response.status === 204 ? null : response.json()
}

function StatCard({ label, value, detail, tone, icon: Icon }) {
  return (
    <article className={`stat-card ${tone}`}>
      <div className="stat-icon"><Icon size={19} strokeWidth={2.2} /></div>
      <div><p>{label}</p><strong>{value}</strong><small>{detail}</small></div>
    </article>
  )
}

function TaskForm({ task, onClose, onSaved }) {
  const [form, setForm] = useState({ title: task?.title || '', description: task?.description || '', status: task?.status || 'todo' })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    if (!form.title.trim()) return setError('Escribe un título para la tarea.')
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
        <div className="modal-heading"><div><span className="eyebrow">Gestión operativa</span><h2>{task ? 'Editar tarea' : 'Nueva tarea'}</h2></div><button type="button" className="icon-button" onClick={onClose} aria-label="Cerrar"><X size={19} /></button></div>
        <label>Título<input autoFocus value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} placeholder="Ej. Revisar conciliación" /></label>
        <label>Descripción<textarea rows="4" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} placeholder="Añade contexto para el equipo" /></label>
        <label>Estado<select value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}><option value="todo">Pendiente</option><option value="in_progress">En curso</option><option value="done">Completada</option></select></label>
        {error && <p className="form-error">{error}</p>}
        <div className="modal-actions"><button type="button" className="button secondary" onClick={onClose}>Cancelar</button><button className="button primary" disabled={saving}>{saving ? <LoaderCircle className="spin" size={17} /> : <Check size={17} />}{task ? 'Guardar cambios' : 'Crear tarea'}</button></div>
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
    setLoading(true); setError('')
    try { const data = await request('/tasks/'); setTasks(data); onCountChange(data.length) } catch (requestError) { setError(requestError.message) } finally { setLoading(false) }
  }
  useEffect(() => { loadTasks() }, [])
  const filtered = tasks.filter((task) => `${task.title} ${task.description}`.toLowerCase().includes(query.toLowerCase()))

  async function removeTask(task) {
    if (!window.confirm(`¿Eliminar “${task.title}”?`)) return
    try { await request(`/tasks/${task.id}/`, { method: 'DELETE' }); setTasks((current) => current.filter((item) => item.id !== task.id)); onCountChange(tasks.length - 1) } catch (requestError) { setError(requestError.message) }
  }
  function savedTask(saved) { setTasks((current) => { const exists = current.some((item) => item.id === saved.id); const next = exists ? current.map((item) => item.id === saved.id ? saved : item) : [saved, ...current]; onCountChange(next.length); return next }); setEditing(null) }

  return <section className="content-section"><div className="section-heading"><div><span className="eyebrow">Seguimiento del equipo</span><h2>Tareas</h2><p>Convierte pendientes en avances visibles.</p></div><button className="button primary" onClick={() => setEditing({})}><Plus size={17} />Nueva tarea</button></div>
    <div className="toolbar"><div className="search-box"><Search size={17} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar tareas..." /></div><button className="button ghost" onClick={loadTasks}><RefreshCw size={16} />Actualizar</button></div>
    {error && <ErrorBanner message={error} onRetry={loadTasks} />}
    {loading ? <LoadingState /> : filtered.length === 0 ? <EmptyState label="No hay tareas que mostrar" /> : <div className="task-list">{filtered.map((task) => <article className="task-row" key={task.id}><div className="task-check">{task.status === 'done' && <Check size={15} />}</div><div className="task-main"><h3>{task.title}</h3><p>{task.description || 'Sin descripción'}</p><small>Actualizada {formatDate(task.updated_at)}</small></div><span className={`status-pill ${statusClass[task.status] || 'gray'}`}>{statusLabels[task.status] || task.status}</span><div className="row-actions"><button className="text-button" onClick={() => setEditing(task)}>Editar</button><button className="danger-button" onClick={() => removeTask(task)} aria-label={`Eliminar ${task.title}`}><Trash2 size={16} /></button></div></article>)}</div>}
    {editing && <TaskForm task={editing.id ? editing : null} onClose={() => setEditing(null)} onSaved={savedTask} />}
  </section>
}

function FinanceView({ type }) {
  const [rows, setRows] = useState([]); const [loading, setLoading] = useState(true); const [error, setError] = useState(''); const [query, setQuery] = useState('')
  const label = type === 'ingresos' ? 'Ingresos' : 'Gastos'
  async function loadRows() { setLoading(true); setError(''); try { setRows(await request(`/${type}/`)) } catch (requestError) { setError(requestError.message) } finally { setLoading(false) } }
  useEffect(() => { loadRows() }, [type])
  const columns = useMemo(() => rows.length ? Object.keys(rows[0]).slice(0, 7) : [], [rows])
  const filtered = rows.filter((row) => Object.values(row).join(' ').toLowerCase().includes(query.toLowerCase()))
  return <section className="content-section"><div className="section-heading"><div><span className="eyebrow">Data warehouse</span><h2>{label}</h2><p>Últimos registros disponibles en Financiera.</p></div><div className="live-tag"><span />Solo lectura</div></div><div className="toolbar"><div className="search-box"><Search size={17} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={`Buscar en ${label.toLowerCase()}...`} /></div><button className="button ghost" onClick={loadRows}><RefreshCw size={16} />Actualizar</button></div>{error && <ErrorBanner message={error} onRetry={loadRows} />}{loading ? <LoadingState /> : filtered.length === 0 ? <EmptyState label="No hay registros disponibles" /> : <div className="table-wrap"><table><thead><tr>{columns.map((column) => <th key={column}>{column.replaceAll('_', ' ')}</th>)}</tr></thead><tbody>{filtered.map((row, index) => <tr key={`${row.NumeroDocumento || index}-${index}`}>{columns.map((column) => <td key={column} title={String(row[column] ?? '')}>{column.toLowerCase().includes('importe') ? formatMoney(row[column]) : column.toLowerCase().includes('fecha') ? formatDate(row[column]) : row[column] ?? '—'}</td>)}</tr>)}</tbody></table></div>}</section>
}

function LoadingState() { return <div className="loading-state"><LoaderCircle className="spin" size={24} /><span>Cargando información...</span></div> }
function EmptyState({ label }) { return <div className="empty-state"><Database size={25} /><span>{label}</span></div> }
function ErrorBanner({ message, onRetry }) { return <div className="error-banner"><span>{message}</span><button onClick={onRetry}>Reintentar</button></div> }

export default function App() {
  const [activeView, setActiveView] = useState('resumen'); const [taskCount, setTaskCount] = useState(0)
  const active = views.find((view) => view.id === activeView)
  return <div className="app-shell"><aside className="sidebar"><div className="brand"><div className="brand-mark"><CircleDollarSign size={22} /></div><div><strong>financiera</strong><span>Centro operativo</span></div></div><div className="workspace-label">Espacio de trabajo</div><nav>{views.map(({ id, label, icon: Icon }) => <button key={id} className={activeView === id ? 'nav-item active' : 'nav-item'} onClick={() => setActiveView(id)}><Icon size={18} /><span>{label}</span>{id === 'tasks' && taskCount > 0 && <b>{taskCount}</b>}</button>)}</nav><div className="sidebar-footer"><div className="profile-dot">JC</div><div><strong>Jairo Ceron</strong><span>Administrador</span></div></div></aside><main className="main"><header className="topbar"><div><span className="breadcrumb">Operaciones / {active.label}</span><h1>{activeView === 'resumen' ? 'Buenos días, Jairo' : active.label}</h1></div><div className="connection"><span />API conectada</div></header>{activeView === 'resumen' ? <Dashboard onNavigate={setActiveView} taskCount={taskCount} /> : activeView === 'tasks' ? <TasksView onCountChange={setTaskCount} /> : <FinanceView type={activeView} />}</main></div>
}

function Dashboard({ onNavigate, taskCount }) {
  return <section className="content-section dashboard"><div className="welcome-panel"><div><span className="eyebrow">Martes, 8 de septiembre de 2026</span><h2>Tu operación, en una sola vista.</h2><p>Revisa el trabajo del equipo y consulta el pulso financiero del día.</p></div><div className="welcome-orbit"><BarChart3 size={68} strokeWidth={1.1} /></div></div><div className="stats-grid"><StatCard label="Tareas activas" value={taskCount || '—'} detail="En tu espacio de trabajo" tone="mint" icon={ClipboardList} /><StatCard label="Ingresos" value="Consulta" detail="Últimos 100 registros" tone="coral" icon={ArrowUpRight} /><StatCard label="Gastos" value="Consulta" detail="Últimos 100 registros" tone="sun" icon={ArrowDownRight} /></div><div className="quick-section"><div className="section-heading compact"><div><span className="eyebrow">Accesos rápidos</span><h2>Explora tus datos</h2></div></div><div className="quick-grid"><button onClick={() => onNavigate('tasks')}><ClipboardList size={22} /><span><strong>Organiza tareas</strong><small>Gestiona el trabajo pendiente</small></span><ArrowUpRight size={17} /></button><button onClick={() => onNavigate('ingresos')}><ArrowUpRight size={22} /><span><strong>Revisa ingresos</strong><small>Consulta datos del warehouse</small></span><ArrowUpRight size={17} /></button><button onClick={() => onNavigate('gastos')}><ArrowDownRight size={22} /><span><strong>Analiza gastos</strong><small>Consulta los últimos movimientos</small></span><ArrowUpRight size={17} /></button></div></div></section>
}
