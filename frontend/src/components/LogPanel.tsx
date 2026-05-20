import { useEffect, useRef } from 'react'
import { useStore } from '../store'
import styles from './LogPanel.module.css'

export default function LogPanel({ taskId, onClose }: { taskId: string; onClose: () => void }) {
  const { tasks } = useStore()
  const task = tasks[taskId]
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [task?.log.length])

  if (!task) return null

  const isDone = ['done', 'error', 'rejected'].includes(task.status)

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <div>
          <div className={styles.title}>{task.name}</div>
          <div className={styles.cmd}>{task.command}</div>
        </div>
        <button className={styles.close} onClick={onClose}>✕ Cerrar</button>
      </div>

      <div className={styles.body}>
        {task.log.length === 0 ? (
          <div className={styles.empty}>
            {task.status === 'pending_approval' && '⏳ Esperando aprobación...'}
            {task.status === 'queued' && '🔵 En cola, iniciando...'}
            {task.status === 'running' && '⚡ Ejecutando...'}
            {isDone &&
            `Sin output${task.exit_code !== null ? ` (exit ${task.exit_code})` : ''}`}
          </div>
        ) : (
          task.log.map((line, i) => (
            <div key={i} className={styles.line}>
              <span className={styles.time}>{line.time}</span>
              <span className={line.text.toLowerCase().includes('error') ? styles.errText : ''}>
                {line.text}
              </span>
            </div>
          ))
        )}

        {isDone && task.claude_result && (
          <div className={styles.resultCard}>
            <div className={styles.resultTitle}>Resultado de Claude</div>
            <div className={styles.resultText}>{task.claude_result}</div>
            <div className={styles.resultMeta}>
              {task.claude_cost_usd != null && (
                <div className={styles.resultMetaItem}>
                  <span className={styles.resultMetaLabel}>Costo</span>
                  <span className={styles.resultMetaValue}>${task.claude_cost_usd.toFixed(4)}</span>
                </div>
              )}
              {task.claude_session_id && (
                <div className={styles.resultMetaItem}>
                  <span className={styles.resultMetaLabel}>Sesión</span>
                  <span className={styles.resultMetaValue}>{task.claude_session_id.slice(0, 16)}…</span>
                </div>
              )}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  )
}
