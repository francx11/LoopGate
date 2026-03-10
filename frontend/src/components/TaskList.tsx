import { useStore, Task } from '../store'
import { api } from '../services/api'
import styles from './TaskList.module.css'

const STATUS_LABEL: Record<string, string> = {
  pending_approval: '⏳ Aprobación',
  queued: '🔵 En cola',
  running: '⚡ Ejecutando',
  done: '✅ Completada',
  error: '❌ Error',
  rejected: '🚫 Rechazada',
}

export default function TaskList({ onOpenLog }: { onOpenLog: (id: string) => void }) {
  const { tasks } = useStore()
  const list = Object.values(tasks).sort((a, b) => b.created_at.localeCompare(a.created_at))

  if (list.length === 0) {
    return (
      <div className={styles.empty}>
        <div className={styles.emptyIcon}>📭</div>
        <div className={styles.emptyTitle}>Sin tareas</div>
        <p>Crea una nueva tarea desde la pestaña + Nueva</p>
      </div>
    )
  }

  const pending = list.filter(t => t.status === 'pending_approval')
  const active  = list.filter(t => ['running', 'queued'].includes(t.status))
  const rest    = list.filter(t => !['pending_approval', 'running', 'queued'].includes(t.status))

  return (
    <div>
      {pending.length > 0 && <>
        <div className={styles.sectionTitle}>⏳ Esperando aprobación</div>
        {pending.map(t => <TaskCard key={t.id} task={t} onOpenLog={onOpenLog} />)}
      </>}
      {active.length > 0 && <>
        <div className={styles.sectionTitle}>⚡ En ejecución</div>
        {active.map(t => <TaskCard key={t.id} task={t} onOpenLog={onOpenLog} />)}
      </>}
      {rest.length > 0 && <>
        <div className={styles.sectionTitle}>Historial</div>
        {rest.map(t => <TaskCard key={t.id} task={t} onOpenLog={onOpenLog} />)}
      </>}
    </div>
  )
}

function TaskCard({ task, onOpenLog }: { task: Task; onOpenLog: (id: string) => void }) {
  async function approve(action: 'approve' | 'reject') {
    await api.approveTask(task.id, action)
  }

  return (
    <div
      className={`${styles.card} ${styles[task.status.replace('_approval', '')]}`}
      onClick={() => onOpenLog(task.id)}
    >
      <div className={styles.cardHeader}>
        <div>
          {task.status === 'running' && <span className={styles.spinner} />}
          <span className={styles.name}>{task.name}</span>
          {task.description && <div className={styles.desc}>{task.description}</div>}
        </div>
        <span className={`${styles.statusBadge} ${styles['status_' + task.status]}`}>
          {STATUS_LABEL[task.status]}
        </span>
      </div>

      <div className={styles.meta}>
        <span className={styles.cmd} title={task.command}>{task.command}</span>
        <span className={styles.time}>{task.created_at}</span>
      </div>

      {task.status === 'pending_approval' && (
        <div className={styles.actions} onClick={e => e.stopPropagation()}>
          <button className={`${styles.btn} ${styles.approve}`} onClick={() => approve('approve')}>
            ✅ Aprobar
          </button>
          <button className={`${styles.btn} ${styles.reject}`} onClick={() => approve('reject')}>
            🚫 Rechazar
          </button>
        </div>
      )}
    </div>
  )
}
