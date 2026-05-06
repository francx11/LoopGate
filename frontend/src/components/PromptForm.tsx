import { useState } from 'react'
import { api } from '../services/api'
import styles from './PromptForm.module.css'

const DIR_KEY = 'lg-last-dir'

export default function PromptForm({ onCreated }: { onCreated: () => void }) {
  const [prompt, setPrompt] = useState('')
  const [dir, setDir] = useState(() => localStorage.getItem(DIR_KEY) ?? '')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function submit() {
    const text = prompt.trim()
    if (!text) { setError('Escribe un prompt'); return }
    setLoading(true)
    setError('')
    try {
      const escapedPrompt = text.replace(/"/g, '\\"')
      const workingDir = dir.trim()
      const command = workingDir
        ? `cd /d "${workingDir}" && claude -p "${escapedPrompt}"`
        : `claude -p "${escapedPrompt}"`

      if (workingDir) localStorage.setItem(DIR_KEY, workingDir)

      await api.createTask({
        name: text.slice(0, 60),
        command,
        description: workingDir ? `Claude Code @ ${workingDir.split(/[\\/]/).pop()}` : 'Prompt Claude Code',
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
        <label className={styles.dirLabel}>Directorio de trabajo</label>
        <input
          className={styles.dirInput}
          type="text"
          placeholder="C:\Users\Francisco\Documents\Projects\MiProyecto"
          value={dir}
          onChange={e => setDir(e.target.value)}
          spellCheck={false}
        />
        <span className={styles.dirHint}>Se recuerda entre sesiones</span>
      </div>

      <textarea
        className={styles.textarea}
        placeholder="Ej: Añade tests unitarios para el módulo de autenticación..."
        value={prompt}
        onChange={e => setPrompt(e.target.value)}
        onKeyDown={onKeyDown}
        rows={6}
        autoFocus
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
