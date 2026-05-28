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
    const token = localStorage.getItem('lg-token') ?? ''

    // Always verify the backend first — checks if auth is required so we
    // never auto-configure with an empty token when SECRET_TOKEN is set.
    fetch('/health', { signal: AbortSignal.timeout(2000) })
      .then(r => (r.ok ? r.json() : Promise.reject()))
      .then((data: { auth_required: boolean }) => {
        if (data.auth_required && !token) return  // show SetupScreen to enter token
        const origin = window.location.origin
        const wsOrigin = origin.replace(/^https:\/\//, 'wss://').replace(/^http:\/\//, 'ws://')
        // If running on Vite dev server (:5173), WS must go directly to the
        // backend port (:8000) — Vite's WS proxy is unreliable in practice.
        const isDev = window.location.port === '5173'
        const wsBase = isDev ? wsOrigin.replace(':5173', ':8001') : wsOrigin
        const freshWs = `${wsBase}/ws`
        // In dev (:5173) always use current origin so API calls go through
        // Vite proxy — a stale localStorage value pointing at :8000 would
        // cause cross-origin requests that CORS blocks.
        const freshApi = isDev ? origin : (api ?? origin)
        const cfg = {
          apiUrl: freshApi,
          wsUrl: freshWs,
          token,
        }
        localStorage.setItem('lg-api', freshApi)
        localStorage.setItem('lg-ws', freshWs)
        setConfig(cfg)
      })
      .catch(() => {})
      .finally(() => setReady(true))
  }, [setConfig])

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
