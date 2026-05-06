import { useState } from 'react'
import { useStore } from '../store'
import TaskList from '../components/TaskList'
import NewTaskForm from '../components/NewTaskForm'
import PromptForm from '../components/PromptForm'
import LogPanel from '../components/LogPanel'
import styles from './Dashboard.module.css'

type Tab = 'tasks' | 'claude' | 'new'

export default function Dashboard() {
  const { connected, tasks, disconnect } = useStore()
  const [tab, setTab] = useState<Tab>('tasks')
  const [logTaskId, setLogTaskId] = useState<string | null>(null)

  const pendingCount = Object.values(tasks).filter(t => t.status === 'pending_approval').length

  return (
    <div className={styles.layout}>
      <header className={styles.header}>
        <div className={styles.logo}>
          <span className={`${styles.dot} ${connected ? styles.online : styles.offline}`} />
          Loopgate
        </div>
        <div className={styles.right}>
          <span className={`${styles.badge} ${connected ? styles.badgeOnline : styles.badgeOffline}`}>
            {connected ? 'ONLINE' : 'OFFLINE'}
          </span>
          <button className={styles.exitBtn} onClick={disconnect}>Salir</button>
        </div>
      </header>

      <nav className={styles.tabs}>
        <button
          className={`${styles.tab} ${tab === 'tasks' ? styles.active : ''}`}
          onClick={() => setTab('tasks')}
        >
          Tareas
          {pendingCount > 0 && <span className={styles.tabBadge}>{pendingCount}</span>}
        </button>
        <button
          className={`${styles.tab} ${tab === 'claude' ? styles.active : ''}`}
          onClick={() => setTab('claude')}
        >
          🤖 Claude
        </button>
        <button
          className={`${styles.tab} ${tab === 'new' ? styles.active : ''}`}
          onClick={() => setTab('new')}
        >
          + Nueva
        </button>
      </nav>

      <main className={styles.content}>
        {tab === 'tasks' && <TaskList onOpenLog={setLogTaskId} />}
        {tab === 'claude' && <PromptForm onCreated={() => setTab('tasks')} />}
        {tab === 'new' && <NewTaskForm onCreated={() => setTab('tasks')} />}
      </main>

      {logTaskId && <LogPanel taskId={logTaskId} onClose={() => setLogTaskId(null)} />}
    </div>
  )
}
