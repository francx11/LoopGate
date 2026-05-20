import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { useStore } from '../store'
import styles from './PromptForm.module.css'

const DIR_KEY = 'lg-last-dir'

interface Project { name: string; path: string }

export default function PromptForm({ onCreated }: { onCreated: () => void }) {
  const [prompt, setPrompt] = useState('')
  const [projects, setProjects] = useState<Project[]>([])
  const [selectedPath, setSelectedPath] = useState(() => localStorage.getItem(DIR_KEY) ?? '')
  const [customPath, setCustomPath] = useState('')
  const [continueSession, setContinueSession] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const { sessions, setSessions, deleteSession } = useStore()

  useEffect(() => {
    api.getProjects()
      .then(list => {
        setProjects(list)
        const saved = localStorage.getItem(DIR_KEY)
        if (!saved && list.length > 0) setSelectedPath(list[0].path)
      })
      .catch(() => {})

    api.getSessions()
      .then(s => setSessions(s))
      .catch(() => {})
  }, [setSessions])

  const isCustom = selectedPath === '__custom__'
  const effectiveDir = isCustom ? customPath.trim() : selectedPath
  const activeSessionId = effectiveDir ? sessions[effectiveDir] : undefined

  // When project changes, default the toggle to ON if a session exists
  useEffect(() => {
    setContinueSession(!!activeSessionId)
  }, [effectiveDir, activeSessionId])

  async function submit() {
    const text = prompt.trim()
    if (!text) { setError('Escribe un prompt'); return }
    setLoading(true)
    setError('')
    try {
      if (effectiveDir) localStorage.setItem(DIR_KEY, selectedPath)
      await api.createClaudePrompt({
        prompt: text,
        project_path: effectiveDir,
        new_session: activeSessionId ? !continueSession : false,
      })
      setPrompt('')
      onCreated()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error al enviar')
    }
    setLoading(false)
  }

  async function handleClearSession() {
    if (!effectiveDir) return
    try {
      await api.clearSession(effectiveDir)
      deleteSession(effectiveDir)
      setContinueSession(false)
    } catch { /* ignore */ }
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) submit()
  }

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <span className={styles.icon}>🤖</span>
        <div>
          <div className={styles.title}>Prompt a Claude Code</div>
          <div className={styles.sub}>El agente ejecutará la instrucción en tu PC local</div>
        </div>
      </div>

      <div className={styles.dirGroup}>
        <label className={styles.dirLabel}>Proyecto</label>
        <select
          className={styles.select}
          value={selectedPath}
          onChange={e => setSelectedPath(e.target.value)}
        >
          <option value="">— Sin directorio —</option>
          {projects.map(p => (
            <option key={p.path} value={p.path}>{p.name}</option>
          ))}
          <option value="__custom__">Ruta personalizada...</option>
        </select>

        {isCustom && (
          <input
            className={styles.dirInput}
            type="text"
            placeholder="C:\ruta\al\proyecto"
            value={customPath}
            onChange={e => setCustomPath(e.target.value)}
            spellCheck={false}
            autoFocus
          />
        )}

        {activeSessionId && (
          <div className={styles.sessionRow}>
            <div className={styles.sessionBadge}>
              <span className={styles.sessionDot} />
              sesión activa · {activeSessionId.slice(0, 8)}
            </div>
            <button className={styles.sessionClear} onClick={handleClearSession} title="Borrar sesión">
              × limpiar
            </button>
          </div>
        )}

        {activeSessionId && (
          <div className={styles.toggleRow}>
            <input
              id="continue-session"
              type="checkbox"
              className={styles.toggleCheck}
              checked={continueSession}
              onChange={e => setContinueSession(e.target.checked)}
            />
            <label htmlFor="continue-session" className={styles.toggleLabel}>
              Continuar sesión anterior
            </label>
          </div>
        )}
      </div>

      <textarea
        className={styles.textarea}
        placeholder="Ej: Añade tests unitarios para el módulo de autenticación..."
        value={prompt}
        onChange={e => setPrompt(e.target.value)}
        onKeyDown={onKeyDown}
        rows={6}
      />

      {error && <p className={styles.error}>{error}</p>}

      <button
        className={styles.btn}
        onClick={submit}
        disabled={loading || !prompt.trim()}
      >
        {loading ? 'Enviando...' : '→ Enviar a Claude Code'}
      </button>

      <p className={styles.hint}>
        Requiere aprobación antes de ejecutar · Ctrl+Enter para enviar
      </p>
    </div>
  )
}
