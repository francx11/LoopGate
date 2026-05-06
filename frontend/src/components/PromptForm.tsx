import { useState, useEffect } from 'react'
import { api } from '../services/api'
import styles from './PromptForm.module.css'

const DIR_KEY = 'lg-last-dir'

interface Project { name: string; path: string }

export default function PromptForm({ onCreated }: { onCreated: () => void }) {
  const [prompt, setPrompt] = useState('')
  const [projects, setProjects] = useState<Project[]>([])
  const [selectedPath, setSelectedPath] = useState(() => localStorage.getItem(DIR_KEY) ?? '')
  const [customPath, setCustomPath] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.getProjects()
      .then(list => {
        setProjects(list)
        // Auto-select saved path if still valid, otherwise select first project
        const saved = localStorage.getItem(DIR_KEY)
        if (!saved && list.length > 0) setSelectedPath(list[0].path)
      })
      .catch(() => {})
  }, [])

  const isCustom = selectedPath === '__custom__'
  const effectiveDir = isCustom ? customPath.trim() : selectedPath

  // Windows paths cannot legally contain these characters.
  // Removing them prevents shell breakout via the cd /d "..." argument.
  function sanitizePath(p: string): string {
    return p.replace(/['"<>|*?&;`$]/g, '').trim()
  }

  async function submit() {
    const text = prompt.trim()
    if (!text) { setError('Escribe un prompt'); return }
    setLoading(true)
    setError('')
    try {
      const escapedPrompt = text.replace(/"/g, '\\"')
      const safeDir = sanitizePath(effectiveDir)
      const command = safeDir
        ? `cd /d "${safeDir}" && claude --dangerously-skip-permissions -p "${escapedPrompt}"`
        : `claude --dangerously-skip-permissions -p "${escapedPrompt}"`

      if (safeDir) localStorage.setItem(DIR_KEY, selectedPath)

      const projectName = projects.find(p => p.path === safeDir)?.name
        ?? safeDir.split(/[\\/]/).pop()
        ?? ''

      await api.createTask({
        name: text.slice(0, 60),
        command,
        description: projectName ? `Claude Code @ ${projectName}` : 'Prompt Claude Code',
      })
      setPrompt('')
      onCreated()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error al enviar')
    }
    setLoading(false)
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
