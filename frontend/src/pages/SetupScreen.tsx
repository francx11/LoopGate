import { useState } from 'react'
import { useStore } from '../store'
import styles from './SetupScreen.module.css'

export default function SetupScreen() {
  const { setConfig } = useStore()
  const [apiUrl, setApiUrl] = useState(localStorage.getItem('lg-api') ?? '')
  const [wsUrl, setWsUrl] = useState(localStorage.getItem('lg-ws') ?? '')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function connect() {
    if (!apiUrl) { setError('Introduce la URL del servidor'); return }
    setLoading(true)
    setError('')
    try {
      const res = await fetch(`${apiUrl.replace(/\/$/, '')}/health`)
      if (!res.ok) throw new Error()
      const baseHost = apiUrl.replace('https://', '').replace('http://', '').split(':')[0]
      const ws = wsUrl || `ws://${baseHost}:8765`
      localStorage.setItem('lg-api', apiUrl)
      localStorage.setItem('lg-ws', ws)
      setConfig({ apiUrl: apiUrl.replace(/\/$/, ''), wsUrl: ws })
    } catch {
      setError('No se pudo conectar. Verifica que el servidor está corriendo.')
    }
    setLoading(false)
  }

  return (
    <div className={styles.wrapper}>
      <div className={styles.card}>
        <div className={styles.logo}>
          <span className={styles.dot} />
          Loopgate
        </div>
        <p className={styles.sub}>Control remoto de tareas para agentes IA</p>

        <div className={styles.group}>
          <label>URL del servidor</label>
          <input
            type="url"
            placeholder="http://localhost:8000"
            value={apiUrl}
            onChange={e => setApiUrl(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && connect()}
          />
          <span className={styles.hint}>Con ngrok: https://abc123.ngrok-free.app</span>
        </div>

        <div className={styles.group}>
          <label>WebSocket (opcional)</label>
          <input
            type="text"
            placeholder="ws://localhost:8765"
            value={wsUrl}
            onChange={e => setWsUrl(e.target.value)}
          />
          <span className={styles.hint}>Se auto-detecta si lo dejas vacío</span>
        </div>

        {error && <p className={styles.error}>{error}</p>}

        <button className={styles.btn} onClick={connect} disabled={loading}>
          {loading ? 'Conectando...' : 'Conectar'}
        </button>
      </div>
    </div>
  )
}