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
            {['done', 'error', 'rejected'].includes(task.status) && 'Sin output'}
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
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
