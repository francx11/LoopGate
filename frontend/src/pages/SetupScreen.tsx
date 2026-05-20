import { useState } from 'react'
import { useStore } from '../store'
import styles from './SetupScreen.module.css'

export default function SetupScreen() {
  const { setConfig } = useStore()
  const [apiUrl, setApiUrl] = useState(localStorage.getItem('lg-api') ?? window.location.origin)
  const [wsUrl, setWsUrl] = useState(localStorage.getItem('lg-ws') ?? '')
  const [token, setToken] = useState(localStorage.getItem('lg-token') ?? '')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function connect() {
    if (!apiUrl) { setError('Introduce la URL del servidor'); return }
    setLoading(true)
    setError('')
    try {
      const base = apiUrl.replace(/\/$/, '')
      const headers: Record<string, string> = {}
      if (token) headers['Authorization'] = `Bearer ${token}`
      const res = await fetch(`${base}/health`, { headers })
      if (!res.ok) throw new Error()
      const ws = wsUrl || base.replace(/^https:\/\//, 'wss://').replace(/^http:\/\//, 'ws://') + '/ws'
      localStorage.setItem('lg-api', base)
      localStorage.setItem('lg-ws', ws)
      localStorage.setItem('lg-token', token)
      setConfig({ apiUrl: base, wsUrl: ws, token })
    } catch {
      setError('No se pudo conectar. Verifica la URL y el token.')
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
            placeholder="http://100.x.x.x:8000"
            value={apiUrl}
            onChange={e => setApiUrl(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && connect()}
          />
          <span className={styles.hint}>Con ngrok: https://abc123.ngrok-free.app</span>
        </div>

        <div className={styles.group}>
          <label>Token de acceso</label>
          <input
            type="password"
            placeholder="SECRET_TOKEN del servidor"
            value={token}
            onChange={e => setToken(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && connect()}
            autoComplete="current-password"
          />
          <span className={styles.hint}>Definido en SECRET_TOKEN del .env del servidor</span>
        </div>

        <div className={styles.group}>
          <label>WebSocket (opcional)</label>
          <input
            type="text"
            placeholder="ws://100.x.x.x:8000/ws"
            value={wsUrl}
            onChange={e => setWsUrl(e.target.value)}
          />
          <span className={styles.hint}>Se auto-detecta desde la URL del servidor</span>
        </div>

        {error && <p className={styles.error}>{error}</p>}

        <button className={styles.btn} onClick={connect} disabled={loading}>
          {loading ? 'Conectando...' : 'Conectar'}
        </button>
      </div>
    </div>
  )
}
