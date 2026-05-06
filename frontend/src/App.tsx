import { useState, useEffect } from 'react'
import { useStore } from './store'
import { useWebSocket } from './hooks/useWebSocket'
import SetupScreen from './pages/SetupScreen'
import Dashboard from './pages/Dashboard'

export default function App() {
  const { config, setConfig } = useStore()
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const api = localStorage.getItem('lg-api')
    const ws = localStorage.getItem('lg-ws')
    const token = localStorage.getItem('lg-token') ?? ''
    if (api && ws) {
      setConfig({ apiUrl: api, wsUrl: ws, token })
      setReady(true)
      return
    }
    // Auto-detect: try connecting to same-origin backend (when served via FastAPI)
    fetch('/health', { signal: AbortSignal.timeout(2000) })
      .then(r => (r.ok ? r.json() : Promise.reject()))
      .then(() => {
        const origin = window.location.origin
        const wsOrigin = origin.replace(/^https:\/\//, 'wss://').replace(/^http:\/\//, 'ws://')
        const cfg = { apiUrl: origin, wsUrl: `${wsOrigin}/ws`, token }
        localStorage.setItem('lg-api', cfg.apiUrl)
        localStorage.setItem('lg-ws', cfg.wsUrl)
        // Keep existing token; user can update it via SetupScreen if needed
        setConfig(cfg)
      })
      .catch(() => {})
      .finally(() => setReady(true))
  }, [])

  if (!ready) return (
    <div style={{
      minHeight: '100dvh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: 'var(--muted)',
      fontFamily: 'var(--font-mono)',
      fontSize: '13px',
    }}>
      Conectando...
    </div>
  )

  return config ? <Main /> : <SetupScreen />
}

function Main() {
  useWebSocket()
  return <Dashboard />
}
